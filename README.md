# MYRTUS Dockerfile Optimization Chatbot

LLM- based Dockerfile optimization, performance analysis and security hardening.

The MYRTUS Dockerfile Optimization Chatbot is a Python application that uses Large Language Models (LLMs) to analyze and optimize Dockerfiles according to user-selected objectives. 
It provides a graphical user interface (GUI) through which users can select an LLM, choose an optimization objective, generate an optimized Dockerfile, and evaluate the resulting container image.

The tool addresses container-level optimization rather than rewriting the application source code inside the image. It aims to improve container configurations while preserving the dependencies and execution requirements needed by the target application.

## Features
- Graphical User Interface: interact with the chatbot through a GUI
- Multiple LLMs: use different code oriented language models through Ollama
- Objective-driven optimization: select one optimization objective at a time
- Dockerfile generation: generate modified Dockerfiles based on the selected objective
- Static analysis: inspect generated configurations 
- Dynamic analysis: evaluate container builds. Analyze build outcomes and relevant metrics, including image size, number of layers, and build time.
- Security hardening: apply Dockerfile security best practices and optionally retrieve vulnerability-related context
- Optional Retrieval-Augmented Generation (RAG): enrich security-oriented generation with information about software packages and known vulnerabilities.
- Experiment evaluation: compare different models and optimization objectives using a common evaluation workflow.

## Optimization objectives
The chatbot supports five optimization objectives:
- Performance: Optimize the Dockerfile for container performance.
- Energy efficiency: Apply optimizations targeting energy efficiency.
- Memory usage: Optimize the container configuration with memory consumption in mind.
- Dependency: Review dependencies and remove unnecessary components where appropriate.
- Secirity hardening: Improve the security posture of the Dockerfile by applying container security best practices.

The selected objective guides the generation process. Only one objective is selected for each optimization run.

## Supported language models
The application integrates LLMs through Ollama
- Qwen2.5-Coder 7B
- DeepSeek-Coder 6.7B
- CodeGemma 7B
- DeepSeek-R1

Model availability depends on the local Ollama installation and the models downloaded by the user.

## Workflow
The typical workflow consists of the following steps:
- Provide the original Dockerfile.
- Choose the LLM to use.
- Select one of the five optimization objectives.
- Select whether to enable static analysis, dynamic analysis, and the optional Retrieval-Augmented Generation (RAG) component.
- Generate an optimized Dockerfile based on the selected model, optimization objective, and configuration options.
- Inspect the generated Dockerfile and, when dynamic analysis is enabled, evaluate the resulting container image through the available build and performance analysis procedures.
- Collect the generated Dockerfile, analysis outputs, and relevant measurements for comparison.

## Security analysis and RAG
The security-hardening objective uses Dockerfile best practices to guide the generation of more secure container configurations.

An optional Retrieval-Augmented Generation (RAG) component can provide additional context about software packages and known vulnerabilities, including OSV/CVE-related information.

When enabled, RAG enriches the generation process with retrieved security context. It is independent of the selected optimization objective and can be enabled or disabled according to the intended workflow.

The retrieved information supports the analysis but does not guarantee that the generated Dockerfile is free from vulnerabilities. Generated configurations should be validated before deployment.

## Requirements
The application requires the following components:
- Python 3
- Ollama 
- Docker Engine or a compatible Docker environment

## Licence
Copyright © University of Sassari.

This project is licensed under the
PolyForm Noncommercial License 1.0.0.

The software is provided for non-commercial use only.
Any use, redistribution, or modification must comply
with the terms of the license.

If you use this software in scientific research,
please acknowledge the University of Sassari.
  
