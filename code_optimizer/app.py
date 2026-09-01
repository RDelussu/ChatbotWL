import streamlit as st
import requests
import json


# todo: ELIMINARE O CMQ NON CARICARE QUESTO FILE SU GIT... NON INFLUENZ IL RESTO
# ===============================
# CONFIG
# ===============================
OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL_OPTIONS = {
                "Qwen 2.5 Coder 7B (lightweight)": {
                    "model": "qwen2.5-coder:7b",
                    "style": "strict"
                },
    
                "DeepSeek Coder 6.7B (lightweight)": {
                    "model": "deepseek-coder:6.7b",
                    "style": "strict_like"
                },
            
                "CodeGemma 7B (lightweight)": {
                    "model": "codegemma:7b",
                    "style": "explanatory"
                },
            
                "Codestral (mid-to-heavy)": {
                    "model": "codestral",
                    "style": "strict_like"
                }
                }

selected_model_label = st.sidebar.selectbox(
    "Select model",
    list(MODEL_OPTIONS.keys())
)

selected_model = MODEL_OPTIONS[selected_model_label]["model"]
selected_style = MODEL_OPTIONS[selected_model_label]["style"]

def get_model_constraints(style, language):

        strict_constraints = f"""
                                Constraints:
                                - Preserve functional behavior
                                - Output ONLY valid {language} code
                                - No explanations
                                - No markdown
                                - No comments outside code
                                - No bullet points
                                - No vulnerability summaries
                                - Return ONLY the final optimized code
                                """
    
        strict_like_constraints = f"""
                                Constraints:
                                - Preserve functional behavior
                                - Output ONLY valid {language} code
                                - Avoid explanations
                                - Avoid markdown
                                - Avoid bullet points
                                - Return only optimized code when possible
                                - DO NOT explain your optimization choices
                                """
    
        explanatory_constraints = f"""
                                Constraints:
                                - Preserve functional behavior
                                - Output valid {language} code
                                - Keep explanations minimal
                                - Prefer concise outputs
                                - Avoid unnecessary markdown
                                """
    
        styles = {
            "strict": strict_constraints,
            "strict_like": strict_like_constraints,
            "explanatory": explanatory_constraints
        }

        return styles.get(style, strict_constraints)
# ===============================
# HELPERS
# ===============================
def normalize_language(language: str) -> str:
    language = language.lower()
    if language in ["docker", "dockerfile"]:
        return "dockerfile"
    return language

# ==================================================
# CAPTURE INFO ANALYSIS - ORIGINAL VS OPTIMIZED FILE
# ==================================================
import io
import contextlib

def capture_output(func, *args, **kwargs):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        func(*args, **kwargs)
    return buffer.getvalue()

# ================================================================
# ENERGY ANALYSIS -- ANALYSIS AND COMPARISON ORIGINAL VS OPTIMIZED
# ================================================================
from energy_analysis import en_static_docker as energy_static_docker
from energy_analysis import en_dynamic_docker as energy_dynamic_docker
    
def compare_energy_static_docker(original, optimized):
    print("ENERGY EFFICIENCY-  Static Dockerfile Comparison ")
    metrics_orig = energy_static_docker(original)
    metrics_opt  = energy_static_docker(optimized)

    for key in metrics_orig:
        change = metrics_opt[key] - metrics_orig[key]
        print(f"{key}: original={metrics_orig[key]}, optimized={metrics_opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Fewer layers or instructions → potential energy savings during build")
    print("- Optimized ordering → better caching and reduced I/O")
    
def compare_energy_dynamic_docker(original, optimized, image_prefix="comp"):
    print(" ENERGY EFFICENCY - Dynamic Dockerfile Comparison ")
    metrics_orig = energy_dynamic_docker(original, f"{image_prefix}_orig")
    metrics_opt  = energy_dynamic_docker(optimized, f"{image_prefix}_opt")

    for key in metrics_orig:
        change = metrics_opt[key] - metrics_orig[key]
        print(f"{key}: original={metrics_orig[key]}, optimized={metrics_opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Smaller image size or fewer layers → potential energy savings")
    print("- Optimized instructions → faster build, reduced storage overhead")

# =============================================
# PERFORMANCE ANALYSIS: ANALYSOS AND COMPARISON
# =============================================
from performance_analysis import perf_static_docker as performance_static_docker
from performance_analysis import perf_dynamic as performance_dynamic

def compare_perf_static_docker(original, optimized):
    metrics_orig = performance_static_docker(original)
    metrics_opt  = performance_static_docker(optimized)

    print("PERFORMACE: Static Dockerfile Comparison")
    for key in metrics_orig:
        change = metrics_opt[key] - metrics_orig[key]
        print(f"{key}: original={metrics_orig[key]}, optimized={metrics_opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Fewer layers → faster build times")
    print("- Optimized instructions → reduced redundant operations")

def compare_perf_dynamic_docker(original, optimized, image_prefix="perf"):
    metrics_orig = performance_dynamic(original, f"{image_prefix}_orig")
    metrics_opt  = performance_dynamic(optimized, f"{image_prefix}_opt")

    print("PERFORMANCE: Dynamic Dockerfile Comparison ")
    for key in metrics_orig:
        change = metrics_opt[key] - metrics_orig[key]
        print(f"{key}: original={metrics_orig[key]}, optimized={metrics_opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Smaller images → faster build and deploy times")
    print("- Fewer layers → improved build efficiency")

# =========================================
# MEMORY ANALYSIS - ANALYSIS AND COMPARISON
# =========================================
from memory_analysis import mem_static_docker as memory_static_docker
from memory_analysis import mem_dynamic_docker as memory_dynamic_docker

def compare_memory_static_docker(original, optimized):
    metrics_orig = memory_static_docker(original)
    metrics_opt  = memory_static_docker(optimized)

    print(" MEMORY USAGE: Static Dockerfile Comparison ")
    for key in metrics_orig:
        change = metrics_opt[key] - metrics_orig[key]
        print(f"{key}: original={metrics_orig[key]}, optimized={metrics_opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Fewer layers → reduced memory footprint during image handling")
    print("- Optimized COPY/RUN instructions → avoid duplicated data in layers")

def compare_memory_dynamic_docker(original, optimized, image_prefix="memory"):
    metrics_orig = memory_dynamic_docker(original, f"{image_prefix}_orig")
    metrics_opt  = memory_dynamic_docker(optimized, f"{image_prefix}_opt")

    print("MEMORY USAGE: Dynamic Dockerfile Comparison")
    for key in metrics_orig:
        change = metrics_opt[key] - metrics_orig[key]
        print(f"{key}: original={metrics_orig[key]}, optimized={metrics_opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Smaller image size → reduced memory footprint at load time")
    print("- Fewer layers → less metadata and memory overhead")

# =============================================
# DEPENDENCY ANALYSIS - ANALYSIS AND COMPARISON
# =============================================
from dependency_analysis import dep_static_docker as dependency_static_docker
from dependency_analysis import dep_dynamic_docker as dependency_dynamic_docker

def compare_dependency_static_docker(original, optimized):
    orig = dependency_static_docker(original)
    opt  = dependency_static_docker(optimized)

    print("DEPENDENCY ANALYSIS: Static Dockerfile Comparison ")
    for key in orig:
        change = opt[key] - orig[key]
        print(f"{key}: original={orig[key]}, optimized={opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Fewer installed packages → reduced dependency footprint")
    print("- Consolidated install commands → simpler and cleaner images")

def compare_dependency_dynamic_docker(original, optimized, image_prefix="deps"):
    orig = dependency_dynamic_docker(original, f"{image_prefix}_orig")
    opt  = dependency_dynamic_docker(optimized, f"{image_prefix}_opt")

    print("DEPENDENCY ANALYSIS: Dynamic Dockerfile Comparison")
    for key in orig:
        change = opt[key] - orig[key]
        print(f"{key}: original={orig[key]}, optimized={opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Smaller image size → fewer dependencies included")
    print("- Reduced layers → fewer dependency-related artifacts")

# ============================================
# SECURITY ANASLYSIS - ANALYSIS AND COMPARISON
# ============================================
from security_analysis import sec_static_docker as security_static_docker
from security_analysis import sec_dynamic_docker as security_dynamic_docker

def compare_security_static_docker(original, optimized):
    orig = security_static_docker(original)
    opt  = security_static_docker(optimized)

    print("SECURITY ANALYSIS – Static Dockerfile")
    for k in orig:
        print(f"{k}: original={orig[k]}, optimized={opt[k]}, change={opt[k] - orig[k]}")

    print("\nInterpretation:")
    print("- Avoiding root user and insecure install patterns improves container security")

def compare_security_dynamic_docker(original, optimized, image_prefix="security"):
    # Build images
    security_dynamic_docker(original, f"{image_prefix}_orig")
    security_dynamic_docker(optimized, f"{image_prefix}_opt")

    # Inspect security properties
    orig = security_dynamic_docker(f"{image_prefix}_orig")
    opt  = security_dynamic_docker(f"{image_prefix}_opt")

    print("SECURITY ANALYSIS – Dynamic Dockerfile")
    for key in orig:
        change = opt[key] - orig[key]
        print(f"{key}: original={orig[key]}, optimized={opt[key]}, change={change}")

    print("\nInterpretation:")
    print("- Running as non-root user improves container isolation")
    print("- Reduced exposed ports lower the external attack surface")

# =====================
# run analysis function
# =====================
def run_selected_analyses(language, original_code, optimized_code, run_energy=False, run_perf=False, run_memory=False, run_deps=False,  
                          run_security=False, run_static=True, run_dynamic=False):

    language_key = normalize_language(language)
    report = {}

    # ENERGY
    if run_energy:
        try:
            if run_static:
                report["energy_static"] = capture_output(compare_energy_static_docker, original_code, optimized_code)
            if run_dynamic:
                report["energy_dynamic"] = capture_output(compare_energy_dynamic_docker, original_code, optimized_code)
        except Exception as e:
            report["energy_error"] = str(e)

    #  PERFORMANCE 
    if run_perf:
        try:
           if run_static:
                report["perf_static"] = capture_output(compare_perf_static_docker, original_code, optimized_code)
            if run_dynamic:
                report["perf_dynamic"] = capture_output(compare_perf_dynamic_docker, original_code, optimized_code)
        except Exception as e:
            report["perf_error"] = str(e)

    # MEMORY
    if run_memory:
        try:
            if run_static:
                report["memory_static"] = capture_output(compare_memory_static_docker, original_code, optimized_code)
            if run_dynamic:
                report["memory_dynamic"] = capture_output(compare_memory_dynamic_docker, original_code, optimized_code)
        except Exception as e:
            report["memory_error"] = str(e)

    # DEPENDENCIES
    if run_deps:
        try:
            if run_static:
                report["deps_static"] = capture_output(compare_dependency_static_docker, original_code, optimized_code)
            if run_dynamic:
                report["deps_dynamic"] = capture_output(compare_dependency_dynamic_docker, original_code, optimized_code)
        except Exception as e:
            report["deps_error"] = str(e)

    # SECURITY
    if run_security:
        try:
            if run_static:
                report["security_static"] = capture_output(compare_security_static_docker, original_code, optimized_code)
            if run_dynamic:
                report["security_dynamic"] = capture_output(compare_security_dynamic_docker, original_code, optimized_code)
        except Exception as e:
            report["security_error"] = str(e)

    return report

# ===============================
# PROMPT GENERATOR
# ===============================
def build_prompt(language, code, optimization_type, check_vulnerabilities, selected_style):
    language_key = normalize_language(language)

    constraints = get_model_constraints(model_style, language)
    base_prompt = f""" You are a senior software engineer specialized in {optimization_type.lower()} optimization.

                    Programming language: {language}

                    Task:
                        Optimize the following code accordingly.
                    
                    {constraints}
                    """

    optimization_prompts = {
                                    "Energy efficiency": """
                            Optimization focus:
                                - Reduce CPU operations
                                - Reduce memory allocations
                                - Avoid redundant computations
                                - Improve cache locality
                            """,
                                    "Performance": """
                            Optimization focus:
                                - Reduce algorithmic complexity
                                - Improve execution speed
                                - Use efficient language-native constructs
                            """,
                                    "Memory usage": """
                            Optimization focus:
                                - Minimize memory allocations
                                - Reuse buffers and objects
                                - Reduce peak memory usage
                            """,
                                    "Dependency optimization": """
                            Optimization focus:
                                - Remove unnecessary dependencies
                                - Prefer standard libraries
                                - Simplify imports
                            """,
                                    "Security hardening": """
                            Optimization focus:
                                - Avoid insecure patterns
                                - Improve input validation
                                - Use safer APIs
                            """
                            }

    vulnerability_prompts = {"dockerfile": 
                             """
                            Security analysis:
                                - Detect usage of latest tag
                                - Detect running as root
                                - Detect missing USER instruction
                                - Detect exposed secrets in ENV
                                - Detect insecure base images
                                - Suggest multi-stage builds
                             """
                            }

    vulnerability_check = ""
    if check_vulnerabilities:
        vulnerability_check = vulnerability_prompts.get(
            language_key,
                                        """
                            Security analysis:
                                - Detect language-specific insecure patterns
                                - Replace unsafe constructs with secure alternatives
                            """
        )

    full_prompt = f"""
                    {base_prompt}
                    {optimization_prompts[optimization_type]}
                    
                    {vulnerability_check}
                    
                    Input code:
                    ```{language_key}
                    {code}'''
                """
    return full_prompt