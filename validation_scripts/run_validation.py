# validation_scripts/run_validation.py
#!/usr/bin/env python3
import os
import yaml
import argparse
from google.cloud import secretmanager
import data_validation as dv

def get_secret(secret_id, project_id):
    """Fetch secret from Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def load_config(config_path, secrets=None):
    """Load and interpolate config with environment variables"""
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    # Replace environment variables
    for key, value in os.environ.items():
        config_content = config_content.replace(f'${{{key}}}', value)
    
    config = yaml.safe_load(config_content)
    
    # Inject secrets if provided
    if secrets:
        for secret_key, secret_value in secrets.items():
            config = replace_secrets(config, secret_key, secret_value)
    
    return config

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--secret', action='append', help='Secret to fetch')
    args = parser.parse_args()
    
    # Fetch secrets
    secrets = {}
    if args.secret:
        for secret_id in args.secret:
            secrets[secret_id] = get_secret(secret_id, os.environ['GCP_PROJECT_ID'])
    
    # Load and run config
    config = load_config(args.config, secrets)
    results = dv.run_validations(config)
    
    # Save results
    results.to_json('validation_results.json')
    print(f"Validation complete. Results saved to validation_results.json")

if __name__ == "__main__":
    main()