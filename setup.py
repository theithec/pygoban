
import setuptools

with open("README.md", "r") as fobj:
    long_description = fobj.read()

setuptools.setup(
    name="pygoban",
    version="0.0.1",
    author="Tim Heithecker",
    author_email="tim.heithecker@gmail.com",
    description="Goboard with gtp and sgf support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/theithec/pygoban",
    packages=setuptools.find_packages(exclude=("tests",)),
    #include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt"
    ],
    python_requires='>=3.8',
    install_requires=[
        'pyqt5>=5.15.2',
    ],
    entry_points={
        "console_scripts": [
            "pygoban=pygoban.startgame:startpygoban",
        ]
    }
)
