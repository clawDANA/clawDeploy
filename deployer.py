import os
import shutil
import argparse
import sys

def setup_deploy(app_name, region, api_key, deploy_type, target, port):
    template_dir = "templates"
    work_dir = f"deploy_{app_name}"
    
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    print(f"[*] Preparing {deploy_type} deployment for {app_name} (Target: {target})...")

    # Dockerfile is needed for both Fly and Local Docker
    if deploy_type == "nullclaw":
        docker_template = os.path.join(template_dir, "nullclaw.Dockerfile")
    else:
        # For OpenClaw we'll need a Dockerfile too if we want local docker
        # For now let's focus on NullClaw as requested
        docker_template = None 

    if docker_template and os.path.exists(docker_template):
        shutil.copy(docker_template, os.path.join(work_dir, "Dockerfile"))

    if target == "fly":
        # Select fly.toml template
        if deploy_type == "nullclaw":
            toml_template = os.path.join(template_dir, "nullclaw.fly.toml")
        else:
            toml_template = os.path.join(template_dir, "openclaw.fly.toml")

        # Process fly.toml
        with open(toml_template, "r") as f:
            content = f.read()
        
        content = content.replace('app = "openclaw"', f'app = "{app_name}"')
        content = content.replace('app = "nullclaw"', f'app = "{app_name}"')
        content = content.replace('primary_region = "iad"', f'primary_region = "{region}"')

        with open(os.path.join(work_dir, "fly.toml"), "w") as f:
            f.write(content)

        # Create Fly setup script
        with open(os.path.join(work_dir, "setup.sh"), "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"fly apps create {app_name} --org personal\n")
            f.write(f"fly secrets set OPENCLAW_GATEWAY_TOKEN={api_key} --app {app_name}\n")
            if deploy_type == "nullclaw":
                 f.write(f"fly secrets set NULLCLAW_API_KEY={api_key} --app {app_name}\n")
            f.write("fly deploy\n")
        
        os.chmod(os.path.join(work_dir, "setup.sh"), 0o755)
        print(f"[!] To deploy to Fly.io, run: cd {work_dir} && ./setup.sh")

    elif target == "docker":
        # Process docker-compose.yml
        compose_template = os.path.join(template_dir, f"{deploy_type}.docker-compose.yml")
        if os.path.exists(compose_template):
            with open(compose_template, "r") as f:
                content = f.read()
            
            content = content.replace('${APP_NAME}', app_name)
            content = content.replace('${API_KEY}', api_key)
            content = content.replace('${PORT}', str(port))

            with open(os.path.join(work_dir, "docker-compose.yml"), "w") as f:
                f.write(content)

            # Create Docker run script
            with open(os.path.join(work_dir, "run.sh"), "w") as f:
                f.write("#!/bin/bash\n")
                f.write("docker compose up -d --build\n")
                f.write(f"echo 'Container {app_name} started on port {port}'\n")
            
            os.chmod(os.path.join(work_dir, "run.sh"), 0o755)
            print(f"[!] To run locally in Docker, run: cd {work_dir} && ./run.sh")

    print(f"[+] Done! Files generated in ./{work_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="clawDeploy Automator")
    parser.add_argument("--name", required=True, help="App name")
    parser.add_argument("--region", default="ams", help="Fly.io region")
    parser.add_argument("--key", required=True, help="API Key / Token")
    parser.add_argument("--type", choices=["openclaw", "nullclaw"], default="nullclaw", help="Deployment type")
    parser.add_argument("--target", choices=["fly", "docker"], default="fly", help="Deployment target")
    parser.add_argument("--port", type=int, default=3000, help="Local port for Docker")

    args = parser.parse_args()
    setup_deploy(args.name, args.region, args.key, args.type, args.target, args.port)
