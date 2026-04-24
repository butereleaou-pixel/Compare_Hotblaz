import subprocess
import threading
import time
import webbrowser
from flask import Flask, request, Response

app = Flask(__name__)
FOLDER = r"D:\Program\Benchmark"

# ---------------------------
# 真·实时流式执行（无报错，无乱码，不掉线）
# ---------------------------
def run_real_time(cmd):
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=FOLDER,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            bufsize=0,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        def generate():
            yield f"PS D:\\Program\\Benchmark> {cmd}\n".encode("utf-8")
            while True:
                data = proc.stdout.read(1)
                if not data:
                    break
                try:
                    yield data.decode("utf-8")
                except:
                    try:
                        yield data.decode("gbk", "ignore")
                    except:
                        yield "?"

            proc.wait()
            yield "\n[COMMAND FINISHED]\n\n".encode("utf-8")

        return Response(generate(), mimetype="text/plain; charset=utf-8")

    except Exception as e:
        return Response(f"ERROR: {str(e)}\n", mimetype="text/plain")

# ---------------------------
# WEB UI
# ---------------------------
HTML = """
<!DOCTYPE html>
<meta charset="UTF-8">
<title>Real-Time PowerShell</title>
<style>
    *{font-family:Consolas,monospace;box-sizing:border-box}
    body{background:#fff;padding:20px;color:#111}
    .container{max-width:900px;margin:auto}
    .box{background:#f2f2f2;padding:15px;border-radius:8px;margin-bottom:15px}
    .title{font-size:18px;font-weight:bold;margin-bottom:10px}
    .select-box{width:100%;padding:10px;border-radius:6px;border:1px solid #ccc;margin-bottom:12px}
    .terminal{
        width:100%;height:440px;background:#f9f9f9;border:1px solid #ccc;
        padding:12px;border-radius:6px;overflow-y:auto;white-space:pre-wrap;
        font-size:14px;margin-bottom:12px;line-height:1.4
    }
    .input-bar{width:100%;padding:10px;border-radius:6px;border:1px solid #ccc;font-size:14px}
</style>

<div class="container">
    <div class="box">
        <div class="title">Real-Time PowerShell Panel</div>
        <select class="select-box" id="preset">
            <option value="">-- 选择命令 --</option>
            <option value="python gpqa.py">python gpqa.py</option>
            <option value="python test.py">python test.py</option>
            <option value="dir">dir</option>
        </select>
    </div>

    <div class="terminal" id="term"></div>
    <input class="input-bar" id="cmd" placeholder="按 Enter 执行">
</div>

<script>
    const term = document.getElementById('term');
    const cmd = document.getElementById('cmd');
    const preset = document.getElementById('preset');

    preset.addEventListener('change', () => {
        cmd.value = preset.value;
        cmd.focus();
    });

    cmd.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            let c = cmd.value.trim();
            if (!c) return;

            cmd.value = '';
            preset.selectedIndex = 0;

            let res = await fetch('/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cmd: c })
            });

            let reader = res.body.getReader();
            let decoder = new TextDecoder('utf-8');

            while (true) {
                let { done, value } = await reader.read();
                if (done) break;
                term.textContent += decoder.decode(value);
                term.scrollTop = term.scrollHeight;
            }
        }
    });
</script>
"""

@app.route('/')
def index():
    return HTML

@app.route('/run', methods=['POST'])
def run():
    data = request.get_json()
    return run_real_time(data['cmd'])

def auto_open():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:7788")

if __name__ == '__main__':
    threading.Thread(target=auto_open, daemon=True).start()
    app.run(host="127.0.0.1", port=7788, debug=False, use_reloader=False)