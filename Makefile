new_venv:
	@pyvenv-3.5 venv

init: new_venv
	@source venv/bin/activate; pip install --upgrade pip
	@source venv/bin/activate; pip install -r pip-req.txt

web:
	@source venv/bin/activate; gunicorn -v; gunicorn -w 4 -b 127.0.0.1:8080 -t 600 app:app
