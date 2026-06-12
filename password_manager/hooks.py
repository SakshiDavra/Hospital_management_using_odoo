from cryptography.fernet import Fernet

def post_init_hook(env):
    icp = env['ir.config_parameter'].sudo()

    if not icp.get_param('password_manager.encryption_key'):
        icp.set_param(
            'password_manager.encryption_key',
            Fernet.generate_key().decode()
        )