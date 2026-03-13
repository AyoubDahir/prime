
import paramiko
import time

hostname = "192.145.173.102"
username = "hussein"
password = "D2cdec4f12##"

commands = [
    "cd frappe-bench && bench --site fullii.com execute frappe.delete_doc --args \"['Report', 'Pharmacy Item Flow & Profit']\""
]

def run_update():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {hostname}...")
        client.connect(hostname, username=username, password=password)
        print("Connected.")

        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            
            if out:
                print(f"STDOUT: {out}")
            if err:
                print(f"STDERR: {err}")

        client.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_update()
