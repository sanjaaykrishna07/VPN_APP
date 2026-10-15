# Quantum-Safe Hybrid VPN Testbed — Docker Gateway

This package containerizes the **cloud gateway/server component** of the project.

## Important architecture note

The complete project has components that are not appropriate for a Linux Docker
container:

- Windows Tkinter GUI
- Windows WinINet/system-proxy automation
- Mobile PWA

This Docker image is therefore intended for the **cloud gateway / server side**.
The client GUI/PWA can connect to the exposed gateway.

## Expected project entry point

The image expects:

    cloud_server.py

to exist in the same project directory.

## Build

    docker build -t quantum-safe-vpn-gateway:latest .

## Run

    docker run --rm -p 8888:8888 quantum-safe-vpn-gateway:latest

## Or use Compose

    docker compose up --build

The gateway will be exposed on:

    http://localhost:8888

For a WebSocket/TLS deployment, configure TLS termination and the public
gateway hostname separately. Do not put private TLS keys into Git.

## GitHub Codespaces

The project can expose port 8888 through Codespaces/Dev Containers.
Set the Codespaces port visibility according to your institution/project
requirements.

## Security

This project is an academic security testbed. Keep DH-16/Shor demonstrations
limited to controlled data and authorized environments. Do not expose an
experimental weak-crypto attack endpoint as a public service.

## Current limitation

The actual source files were not present in the uploaded project materials when
this Docker package was generated. Therefore this is a **ready-to-build Docker
packaging layer**, not a claim that the complete VPN server has already been
compiled into an image here.
