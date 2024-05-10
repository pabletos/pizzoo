from setuptools import setup

setup(
    name="pizzoo",
    version="0.9.0",
    author="Pablo Huet",
    description=(
        "Pizzoo is a library for rendering on pixel matrix screens, with direct support for the Divoom Pixoo64 device, and easy integration for any other one.",
        "It includes full animation buffer manipulation, a micro game engine, as well as XML/HTML like templates compilation.",
    ),
    license="MIT",
    keywords="pixoo, pixoo64, divoom, screen, pixel, matrix, render, buffer, LED matrix, LED, raspberry, raspberry pi",
    url="https://github.com/pabletos/pizzoo#readme",
    packages=['pizzoo'],
    install_requires=[
        'requests ~= 2.31.0',
        'Pillow ~= 10.0.0',
		'bdfparser ~= 2.2.0'
    ],
	classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
    ]
)