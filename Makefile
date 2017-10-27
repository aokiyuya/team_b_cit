default: GUI_for_team_B.py al.png ~/ipaexm.ttf
	python GUI_for_team_B.py

clean:
	touch temp.pyc
	ls | grep *pyc | xargs rm

init:
	apt-get update
	apt-get upgrade
	yes | apt-get install python-setuptools python-pygame python-opengl \
		python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
		build-essential python-pip libgl1-mesa-dev libgles2-mesa-dev zlib1g-dev
	pip install pygments docutils
	pip install --upgrade Cython==0.25.2
	pip install kivy
	python -c "import kivy" || \
		open "https://kivy.org/docs/installation/installation.html" || \
		gnome-open "https://kivy.org/docs/installation/installation.html"

