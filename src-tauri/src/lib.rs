use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Write},
    path::{Path, PathBuf},
    process::{Child, ChildStdin, ChildStdout, Command, Stdio},
    sync::{Arc, Mutex},
};
use tauri::{Manager, State};

struct BackendProcess {
    child: Option<Child>,
    stdin: Option<ChildStdin>,
    stdout: Option<BufReader<ChildStdout>>,
    next_id: u64,
    last_error_was_response: bool,
    project_dir: PathBuf,
    data_dir: PathBuf,
    resource_dir: Option<PathBuf>,
}

impl BackendProcess {
    fn new(app: &tauri::App) -> Self {
        let project_dir = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("src-tauri must have a parent")
            .to_path_buf();
        let resource_dir = app.path().resource_dir().ok();
        let data_dir = app
            .path()
            .app_data_dir()
            .unwrap_or_else(|_| project_dir.clone());
        Self {
            child: None,
            stdin: None,
            stdout: None,
            next_id: 1,
            last_error_was_response: false,
            project_dir,
            data_dir,
            resource_dir,
        }
    }

    fn start(&mut self) -> Result<(), String> {
        if self
            .child
            .as_mut()
            .is_some_and(|child| child.try_wait().ok().flatten().is_none())
        {
            return Ok(());
        }
        self.stop();

        let bundled_backend = self.resource_dir.as_ref().and_then(|dir| {
            [
                dir.join("bus_backend.exe"),
                dir.join("resources").join("bus_backend.exe"),
            ]
            .into_iter()
            .find(|path| path.exists())
        });
        let (program, args, working_dir): (PathBuf, Vec<String>, PathBuf) =
            if let Some(path) = bundled_backend {
                (path, vec![], self.data_dir.clone())
            } else {
                let venv_python = self
                    .project_dir
                    .join(".venv")
                    .join("Scripts")
                    .join("python.exe");
                let python = if venv_python.exists() {
                    venv_python
                } else {
                    PathBuf::from("python")
                };
                let script = self.project_dir.join("bus_backend.py");
                (
                    python,
                    vec![script.to_string_lossy().into_owned()],
                    self.project_dir.clone(),
                )
            };
        std::fs::create_dir_all(&working_dir)
            .map_err(|error| format!("백엔드 데이터 폴더 생성 실패 ({working_dir:?}): {error}"))?;
        if working_dir == self.data_dir {
            let legacy_rules = self.project_dir.join("bus_routing_rules.json");
            let migrated_rules = self.data_dir.join("bus_routing_rules.json");
            if legacy_rules.exists() && !migrated_rules.exists() {
                let _ = std::fs::copy(legacy_rules, migrated_rules);
            }
        }

        let mut command = Command::new(&program);
        command
            .args(args)
            .current_dir(&working_dir)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .env("PYTHONUNBUFFERED", "1")
            .env("PYTHONUTF8", "1")
            .env("PYTHONIOENCODING", "utf-8");
        #[cfg(target_os = "windows")]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command
            .spawn()
            .map_err(|error| format!("Python backend 시작 실패 ({program:?}): {error}"))?;
        let stdin = child
            .stdin
            .take()
            .ok_or("backend stdin을 열 수 없습니다.")?;
        let stdout = child
            .stdout
            .take()
            .ok_or("backend stdout을 열 수 없습니다.")?;
        self.stdin = Some(stdin);
        self.stdout = Some(BufReader::new(stdout));
        self.child = Some(child);
        Ok(())
    }

    fn request_once(&mut self, command: &str, payload: &Value) -> Result<Value, String> {
        self.last_error_was_response = false;
        self.start()?;
        let request_id = self.next_id;
        self.next_id += 1;
        let request = json!({ "id": request_id, "command": command, "payload": payload });
        let stdin = self.stdin.as_mut().ok_or("backend stdin이 없습니다.")?;
        serde_json::to_writer(&mut *stdin, &request).map_err(|error| error.to_string())?;
        stdin.write_all(b"\n").map_err(|error| error.to_string())?;
        stdin.flush().map_err(|error| error.to_string())?;

        let mut line = String::new();
        let read = self
            .stdout
            .as_mut()
            .ok_or("backend stdout이 없습니다.")?
            .read_line(&mut line)
            .map_err(|error| error.to_string())?;
        if read == 0 {
            return Err("Python backend 연결이 종료되었습니다.".into());
        }
        let response: Value = serde_json::from_str(&line)
            .map_err(|error| format!("backend 응답 해석 실패: {error}; {line}"))?;
        if response.get("id").and_then(Value::as_u64) != Some(request_id) {
            return Err("backend 응답 ID가 일치하지 않습니다.".into());
        }
        if response.get("ok").and_then(Value::as_bool) != Some(true) {
            self.last_error_was_response = true;
            return Err(response
                .get("error")
                .and_then(Value::as_str)
                .unwrap_or("backend 오류")
                .to_owned());
        }
        Ok(response.get("data").cloned().unwrap_or(Value::Null))
    }

    fn request(&mut self, command: &str, payload: &Value) -> Result<Value, String> {
        match self.request_once(command, payload) {
            Ok(value) => Ok(value),
            Err(first_error) => {
                if self.last_error_was_response {
                    return Err(first_error);
                }
                self.stop();
                self.request_once(command, payload).map_err(|second_error| {
                    format!("{first_error}\n재시작 후에도 실패: {second_error}")
                })
            }
        }
    }

    fn stop(&mut self) {
        self.stdin.take();
        self.stdout.take();
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

impl Drop for BackendProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

struct BackendState(Arc<Mutex<BackendProcess>>);

#[tauri::command]
async fn backend_request(
    state: State<'_, BackendState>,
    command: String,
    payload: Value,
) -> Result<Value, String> {
    let backend = Arc::clone(&state.0);
    tauri::async_runtime::spawn_blocking(move || {
        let mut process = backend
            .lock()
            .map_err(|_| "backend lock이 손상되었습니다.".to_owned())?;
        process.request(&command, &payload)
    })
    .await
    .map_err(|error| format!("backend worker가 중단되었습니다: {error}"))?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            app.manage(BackendState(Arc::new(Mutex::new(BackendProcess::new(app)))));
            if let Some(window) = app.get_webview_window("main") {
                window.set_zoom(1.0)?;
                #[cfg(target_os = "windows")]
                window.set_shadow(false)?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![backend_request])
        .run(tauri::generate_context!())
        .expect("failed to start Bus Routing Auditor");
}
