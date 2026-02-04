# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, Response, stream_with_context
import os
from werkzeug.utils import secure_filename
import subprocess
import io
import sys
from pathlib import Path
import traceback
import time

PROJECT_DIR = os.path.dirname(__file__)
DATA_FILENAME = '招生数据_clean.csv'
DATA_PATH = os.path.join(PROJECT_DIR, DATA_FILENAME)
OUT_DIR = os.path.join(PROJECT_DIR, 'figures')
UPLOAD_FOLDER = PROJECT_DIR
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.secret_key = 'dev-secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 延迟导入分析模块（确保 Flask 启动时使用本地文件）
import analysis
import Clean_Data


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    # 列出 figures 目录下的图片
    imgs = []
    if os.path.isdir(OUT_DIR):
        for fn in sorted(os.listdir(OUT_DIR)):
            if fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                imgs.append(fn)
    # 读取最近一次操作日志（如果存在）
    log_path = os.path.join(PROJECT_DIR, 'last_action.log')
    log_text = ''
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_text = f.read()
        except Exception:
            log_text = '无法读取日志文件'
    return render_template('index.html', images=imgs, log_text=log_text)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('未选择文件')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('未选择文件')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            # 覆盖项目中的数据文件
            try:
                os.replace(save_path, DATA_PATH)
            except Exception:
                # 在某些系统中 os.replace 可能权限受限，尝试复制
                import shutil
                shutil.copy(save_path, DATA_PATH)
                os.remove(save_path)
            flash('上传并替换数据成功')
            return redirect(url_for('index'))
    return render_template('upload.html')


@app.route('/run_all', methods=['POST'])
def run_all():
    # 运行 analysis.main 来生成所有图表和摘要，并捕获输出到日志
    log_path = os.path.join(PROJECT_DIR, 'last_action.log')
    try:
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = buf_out
        sys.stderr = buf_err
        try:
            analysis.main()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        out = buf_out.getvalue()
        err = buf_err.getvalue()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== ANALYSIS OUTPUT ===\n')
            f.write(out or '')
            if err:
                f.write('\n=== ANALYSIS ERR ===\n')
                f.write(err)

        flash('全部分析已完成，图表已生成，日志已写入 last_action.log')
    except Exception as e:
        # 捕获异常并写入日志
        tb = traceback.format_exc()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== ANALYSIS EXCEPTION ===\n')
            f.write(tb)
        flash('运行分析出错，详情见 last_action.log')
    return redirect(url_for('index'))


@app.route('/crawl_run', methods=['POST'])
def crawl_run():
    """通过运行 Data_request.py 来执行爬取，并捕获命令行输出到日志文件。"""
    log_path = os.path.join(PROJECT_DIR, 'last_action.log')
    try:
        # 使用 Popen 实时读取 stdout/stderr 并写入日志，保证 SSE 能立刻推送
        with open(log_path, 'w', encoding='utf-8') as logf:
            logf.write('=== CRAWL OUTPUT (实时) ===\n')
            logf.flush()

            proc = subprocess.Popen([sys.executable, os.path.join(PROJECT_DIR, 'Data_request.py')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            # 逐行读取并写入日志
            try:
                for line in iter(proc.stdout.readline, ''):
                    if line == '' and proc.poll() is not None:
                        break
                    # 写入并立即刷新，SSE 会读到最新文件内容
                    logf.write(line)
                    logf.flush()
            except Exception:
                # 在读取过程中如果出错，记录并继续等待进程结束
                logf.write('\n=== CRAWL READ ERROR ===\n')
                logf.write(traceback.format_exc())
                logf.flush()

            ret = proc.wait()
            logf.write(f'\n=== CRAWL EXIT CODE: {ret} ===\n')
            logf.flush()

        # 如果爬取生成了招生数据 CSV，自动以子进程运行清洗脚本并追加日志（同样实时写入）
        inp = os.path.join(PROJECT_DIR, '招生数据.csv')
        outp = os.path.join(PROJECT_DIR, '招生数据_clean.csv')
        if os.path.exists(inp):
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write('\n=== CLEAN OUTPUT (实时, 自动) ===\n')
                logf.flush()
                proc2 = subprocess.Popen([sys.executable, os.path.join(PROJECT_DIR, 'Clean_Data.py')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                try:
                    for line in iter(proc2.stdout.readline, ''):
                        if line == '' and proc2.poll() is not None:
                            break
                        logf.write(line)
                        logf.flush()
                except Exception:
                    logf.write('\n=== CLEAN READ ERROR ===\n')
                    logf.write(traceback.format_exc())
                    logf.flush()
                ret2 = proc2.wait()
                logf.write(f'\n=== CLEAN EXIT CODE: {ret2} ===\n')
                logf.flush()
            flash('爬取并清洗完成，日志已写入 last_action.log')
        else:
            flash('爬取完成，但未生成招生数据 CSV，详情见 last_action.log')
    except Exception as e:
        # 将异常写入日志并反馈
        with open(log_path, 'a', encoding='utf-8') as logf:
            logf.write('\n=== CRAWL EXCEPTION ===\n')
            logf.write(traceback.format_exc())
        flash('爬取出错: ' + str(e))
    return redirect(url_for('index'))


@app.route('/clean_run', methods=['POST'])
def clean_run():
    """调用 Clean_Data.clean_file 对 `招生数据.csv` 进行清洗，输出到 `招生数据_clean.csv` 并保存日志。"""
    log_path = os.path.join(PROJECT_DIR, 'last_action.log')
    inp = os.path.join(PROJECT_DIR, '招生数据.csv')
    outp = os.path.join(PROJECT_DIR, '招生数据_clean.csv')
    try:
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            Clean_Data.clean_file(Path(inp), Path(outp))
        finally:
            sys.stdout = old_stdout
        s = buf.getvalue()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== CLEAN OUTPUT ===\n')
            f.write(s)
        flash('清洗完成，日志已写入 last_action.log')
    except Exception as e:
        flash('清洗出错: ' + str(e))
    return redirect(url_for('index'))


@app.route('/plot_school_major', methods=['POST'])
def plot_school_major():
    school = request.form.get('school')
    major = request.form.get('major')
    year_min = int(request.form.get('year_min') or 2020)
    year_max = int(request.form.get('year_max') or 2024)
    log_path = os.path.join(PROJECT_DIR, 'last_action.log')
    try:
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            df = analysis.load_and_clean()
            analysis.plot_school_major_yearly(df, school=school, major=major, year_min=year_min, year_max=year_max)
        finally:
            sys.stdout = old_stdout
        s = buf.getvalue()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== PLOT school-major OUTPUT ===\n')
            f.write(s)
        flash('已生成学校-专业趋势图，日志已写入 last_action.log')
    except Exception:
        tb = traceback.format_exc()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== PLOT school-major EXCEPTION ===\n')
            f.write(tb)
        flash('生成图表出错，详情见 last_action.log')
    return redirect(url_for('index'))


@app.route('/plot_school_majors', methods=['POST'])
def plot_school_majors():
    school = request.form.get('school2')
    majors_raw = request.form.get('majors')
    metric = request.form.get('metric') or '平均分'
    year_min = int(request.form.get('year_min2') or 2020)
    year_max = int(request.form.get('year_max2') or 2024)
    majors = None
    if majors_raw:
        majors = [m.strip() for m in majors_raw.split('\n') if m.strip()]
    log_path = os.path.join(PROJECT_DIR, 'last_action.log')
    try:
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            df = analysis.load_and_clean()
            analysis.plot_school_multiple_majors(df, school=school, majors=majors, metric=metric, year_min=year_min, year_max=year_max)
        finally:
            sys.stdout = old_stdout
        s = buf.getvalue()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== PLOT school-majors OUTPUT ===\n')
            f.write(s)
        flash('已生成学校多专业趋势图，日志已写入 last_action.log')
    except Exception:
        tb = traceback.format_exc()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('=== PLOT school-majors EXCEPTION ===\n')
            f.write(tb)
        flash('生成图表出错，详情见 last_action.log')
    return redirect(url_for('index'))


@app.route('/figures/<path:filename>')
def figures(filename):
    return send_from_directory(OUT_DIR, filename)


@app.route('/stream_log')
def stream_log():
    """SSE endpoint: 每秒检查 last_action.log 的变化并推送内容。"""
    def gen():
        log_path = os.path.join(PROJECT_DIR, 'last_action.log')
        last_text = ''
        while True:
            try:
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    text = ''
            except Exception:
                text = '无法读取日志文件'

            if text != last_text:
                # SSE 格式
                for chunk in (text,):
                    yield f"data: {chunk.replace('\n', '\\n')}\n\n"
                last_text = text
            time.sleep(1)

    # 防止中间代理缓存并保持 Flask 上下文
    return Response(stream_with_context(gen()), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })


if __name__ == '__main__':

    app.run(debug=True, port=5000)
