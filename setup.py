from setuptools import setup

setup(
    name="pizzoo",
    version="0.1.0",
    author="Pablo Huet",
    description=(
        "Pizzoo is a full-fledged library for rendering on pixel matrix screens, with direct support for the Divoom Pixoo64 device.",
        "Additionally any other device can be easily integrated.",
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
        "Development Status :: 3 - Alpha",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
    ]
)