import os
import shutil
import argparse
import sys

def setup_deploy(app_name, region, api_key, deploy_type):
    template_dir = "templates"
    work_dir = f"deploy_{app_name}"
    
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    print(f"[*] Preparing {deploy_type} deployment for {app_name} in {region}...")

    # Select templates
    if deploy_type == "nullclaw":
        toml_template = os.path.join(template_dir, "nullclaw.fly.toml")
        docker_template = os.path.join(template_dir, "nullclaw.Dockerfile")
    else:
        toml_template = os.path.join(template_dir, "openclaw.fly.toml")
        # OpenClaw typically uses the Dockerfile from its own repo, 
        # but we could provide a template here too.
        docker_template = None 

    # Copy and process fly.toml
    with open(toml_template, "r") as f:
        content = f.read()
    
    content = content.replace('app = "openclaw"', f'app = "{app_name}"')
    content = content.replace('app = "nullclaw"', f'app = "{app_name}"')
    content = content.replace('primary_region = "iad"', f'primary_region = "{region}"')

    with open(os.path.join(work_dir, "fly.toml"), "w") as f:
        f.write(content)

    # Copy Dockerfile
    if docker_template:
        shutil.copy(docker_template, os.path.join(work_dir, "Dockerfile"))
    
    # Create a setup script for the user
    with open(os.path.join(work_dir, "setup.sh"), "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"fly apps create {app_name} --org personal\n")
        f.write(f"fly secrets set OPENCLAW_GATEWAY_TOKEN={api_key} --app {app_name}\n")
        if deploy_type == "nullclaw":
             f.write(f"fly secrets set NULLCLAW_API_KEY={api_key} --app {app_name}\n")
        f.write("fly deploy\n")
    
    os.chmod(os.path.join(work_dir, "setup.sh"), 0o755)

    print(f"[+] Done! Files generated in ./{work_dir}")
    print(f"[!] To deploy, run: cd {work_dir} && ./setup.sh")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="clawDeploy Automator")
    parser.add_argument("--name", required=True, help="App name")
    parser.add_argument("--region", default="ams", help="Fly.io region")
    parser.add_argument("--key", required=True, help="API Key / Token")
    parser.add_argument("--type", choices=["openclaw", "nullclaw"], default="nullclaw", help="Deployment type")

    args = parser.parse_args()
    setup_deploy(args.name, args.region, args.key, args.type)
