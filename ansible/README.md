# Ansible Configuration

Shared Ansible configuration for all Containerlab labs.

## Setup

Install collections:
```bash
cd ansible
uv run ansible-galaxy collection install -r requirements.yml
```

## Usage

Run playbooks from the ansible directory:
```bash
cd ansible
uv run ansible-playbook playbooks/your-playbook.yml
```

Or set `ANSIBLE_CONFIG` to use from anywhere:
```bash
export ANSIBLE_CONFIG=./ansible/ansible.cfg
uv run ansible-playbook ansible/playbooks/your-playbook.yml
```
