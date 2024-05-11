from setuptools import setup

long_description = open('#').read()

# https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/
setup(
    name="pizzoo",
    version="0.9.3",
    author="Pablo Huet",
    description="Pizzoo is a easy-to-use library for rendering on pixel matrix screens like the Pixoo64, featuring easy new device integration, animation tools, and XML template rendering support.",
    long_description=long_description,
	long_description_content_type='text/markdown',
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