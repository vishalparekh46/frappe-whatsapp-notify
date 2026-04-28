from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="frappe_whatsapp_notify",
    version="0.0.1",
    description="Send WhatsApp notifications from ERPNext via Twilio",
    author="Vishal Parekh",
    author_email="vishal@aavatto.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
