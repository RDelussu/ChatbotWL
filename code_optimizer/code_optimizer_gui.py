import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ollama import Client
import threading
import os
import difflib
import yaml

import io
import contextlib

# energy
from energy_analysis import en_static_docker as energy_static_docker
from energy_analysis import en_static_k8s as energy_static_k8s

# performance
from performance_analysis import perf_static_docker as performance_static_docker
from performance_analysis import perf_static_k8s as performance_static_k8s # analisi dimanica solo performance
from performance_analysis import perf_dynamic as performance_dynamic

# memory
from memory_analysis import mem_static_docker as memory_static_docker
from memory_analysis import mem_static_k8s as memory_static_k8s

# dependencies
from dependency_analysis import dep_static_docker as dependency_static_docker
from dependency_analysis import dep_static_k8s as dependency_static_k8s

# security
from security_analysis import sec_static_docker as security_static_docker
from security_analysis import sec_static_k8s as security_static_k8s

# rag engine
from rag_engine import CodeRAGEngine

# capture function 
def capture_output(func, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        func(*args)
    return buffer.getvalue()

# -------------
# MODELS
# -------------
AVAILABLE_MODELS = {"Qwen 2.5 Coder 7B (lightweight)": "qwen2.5-coder:7b",
                    "DeepSeek Coder 6.7B (lightweight)": "deepseek-coder:6.7b",
                    "CodeGemma 7B (lightweight)": "codegemma:7b",
                   "DeepSeek R1 (reasoning)": "deepseek-r1:latest",}
# -------------
# OLLAMA CONFIG
# -------------
MODEL_NAME = "qwen2.5-coder:7b"
client = Client()

#---------------------
# chat worker creation
# --------------------
last_optimized_code = ""
chat_history = []
# 
# PROMPT 
# 
def build_prompt(language, optimization_type, code, vulnerability_scan, model, rag_context=None, dynamic_analysis=False):
    security_section = ""
    rag_section = ""
    
    # styles (for prompt) related to the selected/considered model
    if "qwen" in model.lower():
        style = "strict"
    elif "deepseek" in model.lower():
        style = "strict_like"
    elif "codegemma" in model.lower():
        style = "strict_like"
    elif "codestral" in model.lower():
        style = "loose_strict"
    else:
        print("No model style available - falling back to strict_like")
        style = "strict_like"
    
    

    if style == "strict":
        constraints = f"""
                            - Output ONLY valid {language} code
                            - Do NOT include explanations
                            - Do NOT include markdown (no ``` blocks)
                            - Do NOT add text before or after the code
                            - Preserve functional behavior
                       """
    elif style == "strict_like":
        constraints = f"""
                        - Return ONLY the final optimized code
                        - Do NOT include explanations
                        - Do NOT include markdown
                        - Do NOT include comments outside the code
                        - Do NOT wrap the code in ```
                        - Output plain raw code only
                    """
    elif style == "loose_strict":
        constraints = f"""
                        - Output ONLY raw code
                        - NO comments
                        - NO explanations
                        - NO markdown
                        - DO NOT include any text outside the code
                        - DO NOT include sections like "VULNERABILITY REPORT"
                        - DO NOT number anything
                        - DO NOT explain choices
                        - ONLY valid executable code
                    """
    if vulnerability_scan:
        security_section = f""" Security analysis:
                            - Detect usage of known vulnerable or unsafe libraries for {language}
                            - Replace them with safer alternatives when possible
                            
                            After the optimized code, append a section EXACTLY in this formrat:
                            - <library_name>: <reason ot CVE ot unsafe pattern>
                            - <library_name>: <reason>
                            
                            If no vulnerable libraries are found, write:
                            #VULNERABILITY REPORT
                            None
                            """
    if rag_context:
        rag_section = f"""
                        Use the following verified optimization patterns, security fixes, or documentation standards retrieved from your corporate/internal  repository to guide your optimization:
                        {rag_context}
            
            Ensure the generated code aligns with these reference practices if applicable.
                        """

    ### dynamic section (dynamic analysis - True)
    dynamic_section = ""
    if language == 'Kubernetes YAML' and dynamic_analysis:
        dynamic_section = f"""
                The Kubernetes deployment is evaluated through dynamic build performance analysis. 
                Therefore:
                - optimize both Kubernetes YAML configuration and the associated Dockerfile
                - preserve the application behaviour
                - consider container build efficiency: image size reduction, reduction of unnecessary layers, faster build time
                - ensure that the optimized kuberntes configuration remains compatible with the optimized docker image
            
                Return the oprimized Kubernetes YAML followed by the optimized Dockerfile
                """
    return f"""
                You are a senior software engineer specialized in {optimization_type.lower()} optimization.
                
                Programming language: {language}
                
                Task:
                    Optimize the following code accordingly.
                    {dynamic_section}
                    
                {rag_section}
                
                Optimization focus:
                    {optimization_type}
                
                {security_section}
                
                Constraints:
                    {constraints}
                
                Input code:
                ```{language.lower()}
                {code}
            """

#
# SELECT YOUR FILE
#
def select_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        dockerfile_path_var.set(filepath)

# check for dockerfile and yaml file
def detect_file_type(filepath):
    filename = os.path.basename(filepath).lower()

    #docker
    if filename == 'dockerfile' or filename.endswith(".dockerfile"):
        return "dockerfile"
    # yaml 
    if filename.endswith(".yml") or filename.endswith(".yaml"):
        return "yaml"

    if validate_dockerfile(filepath):
        return 'dockerfile'

    if validate_kubernetes_yaml(filepath):
        return 'yaml'
    
    return None

# validate dockerfile and yaml file - check for common instructions
def validate_dockerfile(filepath):
    docker_keywords = {"FROM", "RUN", "COPY", "ADD", "CMD", "ENTRYPOINT", "WORKDIR", "EXPOSE", "ENV", "USER"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        found = 0
        for line in lines:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            instruction = stripped.split()[0].upper()
            if instruction in docker_keywords:
                found += 1
        return found > 0

    except Exception:
        return False

# validate yaml file - check
def validate_kubernetes_yaml(filepath):

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
        if not docs:
            return False
       
        for doc in docs:
           if not isinstance(doc, dict):
               continue
           if ("apiVersion" in doc and "kind" in doc and "metadata" in doc):
               return True
        return False
    except Exception:
        return False

# 
def validate_input_file(filepath, selected_language):
    filetype = detect_file_type(filepath)

    if 'dockerfile' in selected_language.lower() and filetype != 'dockerfile':
       return False, "Expected a Dockerfile, but detected a YAML or unknown file."
    if 'kubernetes yaml' in selected_language.lower() and filetype != 'yaml':
       return False, "Expected a Kubernetes YAML, but detected a Dockerfile or unknown file"

    if filetype == "dockerfile":
        return validate_dockerfile(filepath), "dockerfile"
    elif filetype == "yaml":
        if not dockerfile_path_var.get():
            messagebox.showerror("Error", "Please select the associated Dockerfile.")
            return False, "Associated Dockerfile required."
        return validate_kubernetes_yaml(filepath), "kubernetes_yaml"
    
    return False, "Unknown file format."
#
# COLOR DIFF FILE
#
def insert_colored_diff(diff_lines):
    diff_text.config(state=tk.NORMAL)
    diff_text.delete("1.0", tk.END)

    for line in diff_lines:
        if line.startswith("+") and not line.startswith("+++"):
            diff_text.insert(tk.END, line + "\n", "added")
        elif line.startswith("-") and not line.startswith("---"):
            diff_text.insert(tk.END, line + "\n", "removed")
        elif line.startswith("@@") or line.startswith("---") or line.startswith("+++"):
            diff_text.insert(tk.END, line + "\n", "header")
        else:
            diff_text.insert(tk.END, line + "\n")
    
    diff_text.config(state=tk.DISABLED)

#
# copy the optimized output
#
def copy_optimized_code():
    code = output_text.get("1.0", tk.END).strip()
    if not code:
        messagebox.showwarning("Copy", "No optimized code to copy.")
        return

    root.clipboard_clear()
    root.clipboard_append(code)
    root.update()  # mantiene il clipboard
    messagebox.showinfo("Copy", "Optimized code copied to clipboard.")

# function for run_analysis
def add_analysis_result(results, mode, category, content):
    
    if mode not in results or not isinstance(results[mode], dict):
        results[mode] = {}

    results[mode][category] = content
# 
# function for runing the analysis
#
def run_analysis(language, original_code, optimized_code, log_callback):
    import traceback
    is_yaml = language_var.get() == 'Kubernetes YAML'

    results = {"model":model_var.get(), 
              "static": {},
              "dynamic": {}
              }
    def safe_run(mode, category, func, *args):
        try:
            result = capture_output(func, *args)
            add_analysis_result(results, mode, category, result)
        except Exception as e:
            add_analysis_result(results, mode, category, f"Error: {e}")

    # ENERGY
    if run_energy_var.get():
        log_callback("Running Energy Analysis...")
        # static
        if is_yaml:
            safe_run("static", "energy", energy_static_k8s.run, original_code, optimized_code)
        else:
            safe_run("static", "energy", energy_static_docker.run, original_code, optimized_code)


    # PERFORMANCE
    if run_perf_var.get():
        log_callback("Running Performance Analysis...")
        # static
        if run_static_var.get():
            if is_yaml:
                safe_run("static", "performance", performance_static_k8s.run, original_code, optimized_code)
            else:
                safe_run("static", "performance", performance_static_docker.run, original_code, optimized_code)

    # dynamic
    if run_dynamic_var.get():
        log_callback("Running DYNAMIC Performance Analysis...")
        build_context = os.path.dirname(dockerfile_path_var.get())
        safe_run("dynamic", "performance", performance_dynamic.run, original_code, optimized_code, build_context)
    
    # MEMORY
    if run_memory_var.get():
        log_callback("Running STATIC Memory Analysis...")
        # static
        if is_yaml:
            safe_run("static", "memory", memory_static_k8s.run, original_code, optimized_code)
        else:
            safe_run("static", "memory", memory_static_docker.run, original_code, optimized_code)


    # DEPENDENCY 
    if run_deps_var.get():
        log_callback("Running STATIC Dependency Analysis...")
        #static
        if is_yaml:
            safe_run("static", "dependency", dependency_static_k8s.run, original_code, optimized_code)
        else:
            safe_run("static", "dependency", dependency_static_docker.run, original_code, optimized_code)

    
    # SECURITY    
    is_yaml = "yaml" in language.lower()
    if run_security_var.get():
        log_callback("Running Security Analysis...")

        status_text.config(state=tk.NORMAL)
        status_text.delete("1.0", tk.END)
        status_text.insert(tk.END, f"[MODEL] {model_var.get()}")
        status_text.insert(tk.END, "[STATUS] Optmization complete.\n\n")
        status_text.insert(tk.END, "Please wait, running package vulnerability check online...\n")
        status_text.insert(tk.END, "Fetching live data from OSV database, this may take a few seconds...\n\n")
        status_text.config(state=tk.DISABLED)
        status_text.update_idletasks()
        
        # static
        if run_static_var.get():
            if is_yaml:
                safe_run("static", "security", security_static_k8s.run, original_code, optimized_code)
            else:
                safe_run("static", "security", security_static_docker.run, original_code, optimized_code)
        # dynamic
        # if run_dynamic_var.get():
        #     safe_run("dynamic", "security", security_dynamic_docker.run, original_code, optimized_code)
    
    return results
#
# LOGIC BEHIND THE OPTIMIZATION
#
def run_optimization():
    clear_chat()
    filepath = dockerfile_path_var.get()
    build_context = os.path.dirname(filepath)
    language = language_var.get()
    optimization = optimization_var.get()
    vulnerability_scan = vulnerability_var.get()
    selected_label = model_var.get()
    model = AVAILABLE_MODELS[selected_label]

    rag_context = None
    rag_enabled = rag_enabled_var.get()

    if not selected_label or selected_label not in AVAILABLE_MODELS:
        messagebox.showerror("Error", "Please select a valid model first.")
        
    if not filepath or not os.path.isfile(filepath):
        messagebox.showerror("Error", "Please select a valid input file first.")
    valid, message_or_type = validate_input_file(filepath, language)

    if not valid:
        messagebox.showerror("Invalid File / Language Mismatch", f"Mismatch error: {message_or_type}")
        return
    try:
        if language == 'Dockerfile':
            with open(filepath, "r", encoding="utf-8") as f:
                original_code = f.read()
        elif language == 'Kubernetes YAML':
            with open(filepath, "r", encoding="utf-8") as f:
                original_yaml = f.read()
                if run_dynamic_var.get():
                    docker_path = dockerfile_path_var.get()
                    if not docker_path or not os.path.isfile(docker_path):
                        messagebox.showerror("Error", "Dynamic analysis for Kubernetes requires the associated Dockerfile.")
                        return
                    with open(docker_path, "r", encoding="utf-8") as f:
                        original_docker = f.read()

                    original_code = f"""
                        ### Kubernetes YAML
                        {original_yaml}
                        
                        ### Dockerfile
                        {original_docker}
                        """
                else:
                    original_code = original_yaml

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file:\n{e}")
        return
    
    output_text.delete("1.0", tk.END)
    diff_text.config(state=tk.NORMAL)
    diff_text.delete("1.0", tk.END)
    diff_text.config(state=tk.DISABLED)

    status_text.config(state=tk.NORMAL)
    status_text.delete("1.0", tk.END)
    status_text.insert(tk.END, 
                       f"[MODEL] {model} \n"
                       f"[STATUS] Optimization started...\n\n")
    status_text.config(state=tk.DISABLED)

    
    if rag_enabled:
        status_text.config(state=tk.NORMAL)
        status_text.insert(tk.END, "[RAG] Fetching active CVEs from online vulnerability database...\n") 
        status_text.config(state=tk.DISABLED)
        try:
            rag_engine = CodeRAGEngine()
            pkgs = rag_engine.extract_packages(original_code, language)
            status_text.config(state=tk.NORMAL)
            if pkgs:
                for p in pkgs:
                    status_text.insert(tk.END, f"Querying for '{p['name']}' version '{p['version']}\n")
            else:
                status_text.insert(tk.END, "No specific base images/packages parsed from static text.\n")
            status_text.config(state=tk.DISABLED)
            status_text.update_idletasks()
            rag_context = rag_engine.retrieve_context(original_code, language=language, n_results=10)
            status_text.config(state=tk.NORMAL)

            if "SECURITY ALERT" in rag_context:
                status_text.insert(tk.END, "[RAG RESULT] Live CVE data injected into LLM prompt!\n\n")
            else:
                status_text.insert(tk.END, "[RAG RESULT] DB completed with 0 critical vulnerabilities found.\n\n")
        except Exception as e:
            status_text.config(state=tk.NORMAL)
            status_text.insert(tk.END, f"[RAG ERROR] Online DB contact failed: {e} \n\n")
            status_text.config(state=tk.DISABLED)
            
    status_text.config(state=tk.NORMAL)
    status_text.insert(tk.END, "[OPTIMIZER - STEP 2] Contacting Ollama for code optimization...\n")
    status_text.config(state=tk.DISABLED)
    status_text.update_idletasks()
    prompt = build_prompt(language, optimization, original_code, vulnerability_scan, model, rag_context, dynamic_analysis=(language == 'Kubernetes YAML' and run_dynamic_var.get()))
    messages = [{"role":"user", "content":prompt}]
    def worker():
        global last_optimized_code, chat_history
        optimized_code = ""
        clean_code = ""
        vulnerable_libs = []

        def log_to_status(msg):
            root.after(0, lambda: [status_text.config(state=tk.NORMAL),
                                   status_text.insert(tk.END, msg + "\n"),
                                   status_text.config(state=tk.DISABLED),
                                   status_text.see(tk.END)])
        
        try: 
            root.after(0, lambda: update_model_status(f"Model: {model} - Status: Generating...", "dark orange"))

            for part in client.chat(model=model, messages=[{"role": "user", "content": prompt}], stream=True):
                content = part.get('message', {}).get('content') if isinstance(part, dict) else getattr(part.message, 'content', None)

                if content:
                    optimized_code += content
            if not optimized_code.strip():
                log_to_status("Model returned empty output.")
                root.after(0, lambda: update_model_status(f"Model: {model} - Status: Idle", "gray"))
                return
            optimized_code_full = optimized_code.strip()
            extra_notes = []

            marker = "# VULNERABILITY REPORT"
            if vulnerability_scan and marker.lower() in optimized_code_full.lower():
                parts = optimized_code_full.split(marker, 1)
                optimized_code_full = parts[0].strip()
                report_part = parts[1].strip()

                for line in report_part.splitlines():
                    line = line.strip()
                    if line and line.lower() != 'none' and line.startswith('-'):
                        vulnerable_libs.append(line[1:].strip())

            # clean_code = optimized_code_full
            # if "'''" in optimized_code_full:
            #     blocks = optimized_code_full.split("'''")
            #     code_candidates = [blocks[i].strip() for i in range(1, len(blocks), 2)]
            #     if code_candidates:
            #         clean_code = "\n\n".join(code_candidates)
            clean_code = optimized_code_full.strip()
            # cerchiamo di pulire bene il codice..
            if clean_code.startswith("'''"):
                lines = clean_code.split("'''")

                if lines and lines[0].strip().startswith("'''"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "'''":
                    lines = lines[:-1]
                clean_code = "\n".join(lines).strip()
            lines = clean_code.splitlines()
            real_code_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('**') or stripped.lower().startswith('security') or stripped.lower().startswith('recommend') or len(stripped.split())>12 or line.lower() == 'none':
                    extra_notes.append(line)
                else:
                    real_code_lines.append(line)
            clean_code = '\n'.join(real_code_lines).strip()
            last_optimized_code = clean_code
            chat_history = []

            diff = list(difflib.unified_diff(original_code.splitlines(), clean_code.splitlines(), fromfile='original', tofile='optimized', lineterm=''))

            def update_ui_success():
                output_text.config(state=tk.NORMAL)
                output_text.delete('1.0', tk.END)
                output_text.insert(tk.END, clean_code if clean_code else 'No optimized code returned.')

                insert_colored_diff(diff)

                status_text.config(state=tk.NORMAL)
                if clean_code == original_code.strip():
                    status_text.insert(tk.END, 'Code already optimized. No changes applied.\n')
                else:
                    status_text.insert(tk.END, 'Optimization completed.\n')

                if extra_notes:
                    status_text.insert(tk.END, "\nModel notes moved from the code output:\n")
                    for note in extra_notes:
                        status_text.insert(tk.END, f"{note}\n")
                if vulnerability_scan:
                    status_text.insert(tk.END, "\nVulnerability Report:\n")
                    if not vulnerable_libs:
                        status_text.insert(tk.END, "No vulnerable libraries detected.\n")
                    else:
                        for lib in vulnerable_libs:
                            status_text.insert(tk.END, f" - {lib}\n")
                status_text.config(state=tk.DISABLED)

            root.after(0, update_ui_success)

            # analysis - pipeline
            analysis_results = run_analysis(language, original_code, clean_code, log_to_status)
            
            def update_ui_analysis():
                status_text.config(state=tk.NORMAL)
                status_text.insert(tk.END, f"\n -------------- PIPELINE ANALYSIS REPORT --------------\n")
                status_text.insert(tk.END, f"MODEL: {model}\n\n")
                if analysis_results.get("static"):
                    status_text.insert(tk.END, "----- STATIC ANALYSIS CHECKS -----\n\n")
                    for category, result in analysis_results["static"].items():
                        status_text.insert(tk.END, f"[{category.upper()}]\n{result}\n")
                if analysis_results.get("dynamic"):
                    status_text.insert(tk.END, "----- DYNAMIC ANALYSIS CHECKS -----\n\n")
                    for category, result in analysis_results["dynamic"].items():
                        status_text.insert(tk.END, f"[{category.upper()}]\n{result}\n")
                status_text.insert(tk.END, "-------------- END REPORT --------------\n")
                status_text.config(state=tk.DISABLED)
                status_text.see(tk.END)
            root.after(0, update_ui_analysis)
            root.after(0, lambda: update_model_status(f"Model: {model} - Status: Done", "green"))

        except Exception as e:
            root.after(0, lambda err=e: messagebox.showerror("Error", str(e)))
            root.after(0, lambda: update_model_status("Model: Error", "red"))

    threading.Thread(target=worker, daemon=True).start()

    ### chat wokrer
def chat_worker(user_msg, modify_request=False):
    global chat_history, last_optimized_code

    if not last_optimized_code:
        return

    selected_label = model_var.get()
    model = AVAILABLE_MODELS[selected_label]
    
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, f"[MODEL: {model}]\n", model)
    chat_display.config(state=tk.DISABLED)
    
    if 'codegemma' in model.lower():
        model = 'deepseek-r1'
   
    if modify_request:
        system_prompt = f"""
        You are modifying existing code.
    
                            CURRENT CODE:
                            {last_optimized_code}
                            
                            RULES:
                            - Apply the requested modification
                            - Return ONLY the FULL updated code
                            - No explanations
                            - No markdown
                            """
    else:
        system_prompt = f"""You are a helpful programming assistant.
                            
                            You are given a code context:
                            
                            {last_optimized_code}
                            
                            Rules:
                            - If the user is asking a QUESTION, explain in natural language.
                            - If the user explicitly asks to MODIFY or FIX code, return ONLY the updated code.
                            - Do NOT return code unless requested.
                            """

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_msg})

    def run_chat_async():
        global last_optimized_code
        try:
            response_text = ""
            for part in client.chat(model=model, messages=messages, stream=True):
                content = part.get("message", {}).get("content") if isinstance(part, dict) else getattr(part.message, "content", None)
                if content:
                    response_text += content
            def update_chat_ui():
                global last_optimized_code
                if modify_request:
                    old_code = last_optimized_code
                    clean_code = response_text.strip()
                    last_optimized_code = clean_code
                    
                    output_text.config(state=tk.NORMAL)
                    output_text.delete("1.0", tk.END)
                    output_text.insert(tk.END, clean_code)
                    output_text.config(state=tk.DISABLED)
    
                    diff = list(difflib.unified_diff(old_code.splitlines(), clean_code.splitlines(), fromfile="previous", tofile="updated", lineterm=""))
                    insert_colored_diff(diff)
            
                    chat_display.config(state=tk.NORMAL)
                    chat_display.insert(tk.END, "Code updated successfully.\n\n", "assistant")
                    chat_display.config(state=tk.DISABLED)
                else:
                    chat_display.config(state=tk.NORMAL)
                    chat_display.insert(tk.END, response_text + "\n\n", "assistant")
                    chat_display.config(state=tk.DISABLED)
                
                chat_display.see(tk.END)
                chat_history.append({"role": "user", "content": user_msg})
                chat_history.append({"role": "assistant", "content": response_text})
        
            root.after(0, update_chat_ui)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Chat error", str(e)))
    
        threading.Thread(target=run_chat_async, daemon=True).start()

def update_model_status(text, color="black"):
    model_status_label.config(text=text, foreground=color)

# ========= root ==========
root = tk.Tk()
root.title("Code Optimizer & Security Scanner")
root.geometry("1200x1000")

# ======== variables ============
language_var = tk.StringVar(value="Dockerfile")
optimization_var = tk.StringVar(value="Performance")
input_file_var = tk.StringVar()
dockerfile_path_var = tk.StringVar() #compare solo se yaml è selezionato
vulnerability_var = tk.BooleanVar(value=True)
model_var = tk.StringVar(value="Qwen 2.5 Coder 7B (lightweight)")

run_static_var = tk.BooleanVar(value=True)
run_dynamic_var = tk.BooleanVar(value=False)

run_energy_var = tk.BooleanVar(value=False)
run_perf_var = tk.BooleanVar(value=False)
run_memory_var = tk.BooleanVar(value=False)
run_deps_var = tk.BooleanVar(value=False)
run_security_var = tk.BooleanVar(value=False)

rag_enabled_var = tk.BooleanVar(value=False)

# =========== top bar ===============
top = ttk.Frame(root, padding=10)
top.pack(fill=tk.X)

ttk.Label(top, text="Language").pack(side=tk.LEFT)
ttk.Combobox(top, textvariable=language_var, values=["Dockerfile", "Kubernetes YAML"], width=16, state="readonly").pack(side=tk.LEFT, padx=5)

ttk.Label(top, text="Optimization").pack(side=tk.LEFT)
ttk.Combobox(top, textvariable=optimization_var,
             values=["Performance", "Energy efficiency", "Memory usage", "Dependency optimization", "Security hardening"],
             width=25, state="readonly").pack(side=tk.LEFT, padx=5)

ttk.Label(top, text="Model").pack(side=tk.LEFT)
ttk.Combobox(top, textvariable=model_var, values=list(AVAILABLE_MODELS.keys()), width=40, state="readonly").pack(side=tk.LEFT, padx=5)

ttk.Button(top, text="Optimize", command=run_optimization).pack(side=tk.RIGHT)

model_status_label = ttk.Label(top, text="Model: Idle", foreground="gray")
model_status_label.pack(side=tk.RIGHT, padx=10)

# ============ file ===============
file_frame = ttk.Frame(root, padding=5)
file_frame.pack(fill=tk.X)

ttk.Entry(file_frame, textvariable=dockerfile_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
ttk.Button(file_frame, text="Browse", command=select_file).pack(side=tk.RIGHT)

# ========= options ========
options = ttk.Frame(root, padding=5)
options.pack(fill=tk.X)

tk.Checkbutton(options, text="Static", variable=run_static_var).pack(side=tk.LEFT, padx=2)
tk.Checkbutton(options, text="Dynamic (Build Performance)", variable=run_dynamic_var).pack(side=tk.LEFT, padx=2)
#ttk.Label(options, text="Dynamic analysis - docker image build performance (time, size, layers)", foreground='gray').pack(side=tk.LEFT, padx=10)
tk.Checkbutton(options, text="Vulnerability Scan", variable=vulnerability_var).pack(side=tk.LEFT, padx=2)

ttk.Separator(options, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

tk.Checkbutton(options, text="Energy", variable=run_energy_var).pack(side=tk.LEFT)
tk.Checkbutton(options, text="Performance", variable=run_perf_var).pack(side=tk.LEFT)
tk.Checkbutton(options, text="Memory", variable=run_memory_var).pack(side=tk.LEFT)
tk.Checkbutton(options, text="Dependencies", variable=run_deps_var).pack(side=tk.LEFT)
tk.Checkbutton(options, text="Security", variable=run_security_var).pack(side=tk.LEFT)

# ========= rag options ==========
rag_check = tk.Checkbutton(root, text="Enable RAG Enhancement", variable=rag_enabled_var, font=('Arial', 10, 'bold'))
rag_check.pack(anchor=tk.W, padx=10, pady=2)

# ========= status ============
status_text = tk.Text(root, height=10, state=tk.DISABLED, bg="#f5f5f5", font=("Consolas", 10))
status_text.pack(fill=tk.X, padx=10, pady=5)

# ======== main area ==========
paned = tk.PanedWindow(root, orient=tk.VERTICAL)
paned.pack(fill=tk.BOTH, expand=True)

main = ttk.Frame(paned)

left = ttk.Frame(main)
right = ttk.Frame(main)

left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# ---- OUTPUT ----
left.grid_rowconfigure(1, weight=1)
left.grid_columnconfigure(0, weight=1)

header_left = ttk.Frame(left)
header_left.grid(row=0, column=0, sticky="ew")
header_left.grid_columnconfigure(0, weight=1)
header_left.grid_columnconfigure(1, weight=0)
header_left.grid_columnconfigure(2, weight=1)

ttk.Label(header_left, text="Optimized Code").grid(row=0, column=1)
ttk.Button(header_left, text="Copy", command=copy_optimized_code).grid(row=0, column=2, sticky="e", padx=5)

output_text = tk.Text(left, font=("Consolas", 10))
output_text.grid(row=1, column=0, sticky="nsew")

# ===== diff ========
right.grid_rowconfigure(1, weight=1)
right.grid_columnconfigure(0, weight=1)

header_right = ttk.Frame(right)
header_right.grid(row=0, column=0, sticky="ew")
header_right.grid_columnconfigure(0, weight=1)
header_right.grid_columnconfigure(1, weight=0)
header_right.grid_columnconfigure(2, weight=1)

ttk.Label(header_right, text="Diff (Original vs Optimized)").grid(row=0, column=1)

diff_text = tk.Text(right, font=("Consolas", 10))
diff_text.grid(row=1, column=0, sticky="nsew")

diff_text.tag_config("added", foreground="green")
diff_text.tag_config("removed", foreground="red")
diff_text.tag_config("header", foreground="gray")

# ========== chat ============
chat_frame = ttk.Frame(paned, padding=10)
paned.add(main, stretch="always")
paned.add(chat_frame)
paned.paneconfig(chat_frame, minsize=150)

ttk.Label(chat_frame, text="Chat with model").pack(anchor="w")

chat_display = tk.Text(chat_frame, height=8, state=tk.DISABLED, font=("Consolas", 10))
chat_display.pack(fill=tk.BOTH, expand=True)

chat_display.tag_config("user", foreground="#1f77ff", font=("Consolas", 10, "bold"))
chat_display.tag_config("assistant", foreground="#2ca02c")

ttk.Label(chat_frame, text="Write your message here:").pack(anchor="w")

chat_input = ttk.Frame(chat_frame)
chat_input.pack(fill=tk.X, pady=5)

chat_entry = tk.Text(chat_input, height=3, wrap="word", font=("Consolas", 11))
chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
chat_entry.focus_set()

def is_code_request(msg):
    keywords = ["modify", "change", "optimize", "rewrite", "refactor", "fix", "improve", "update", "convert", "add", "remove"]
    return any(k in msg.lower() for k in keywords)

def clear_chat():
    global chat_history
    chat_history = []
    chat_display.config(state=tk.NORMAL)
    chat_display.delete("1.0", tk.END)
    chat_display.config(state=tk.DISABLED)

def send_chat():
    msg = chat_entry.get("1.0", tk.END).strip()
    modify_request = is_code_request(msg)
    if not msg:
        return
    if not last_optimized_code:
        messagebox.showwarning("Chat", "Run optimization first!")
        return

    chat_entry.delete("1.0", tk.END)
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, f"You: {msg}\n", "user")
    chat_display.config(state=tk.DISABLED)

    chat_worker(msg, modify_request)

def on_enter(event):
    if event.state & 0x1: # Shift+Enter per andare a capo
        return
    send_chat()
    return "break"

chat_entry.bind("<Return>", on_enter)
ttk.Button(chat_input, text="Send", command=send_chat).pack(side=tk.RIGHT)

# =========== start ===========
root.mainloop()

