from pathlib import Path

from setuptools import setup


def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", "\n")
    buf = []

    for filename in filenames:
        with open(filename, encoding=encoding) as f:
            buf.append(f.read())

    return sep.join(buf)


this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

setup(
    name="punq",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    url="http://github.com/bobthemighty/punq",
    license="MIT",
    author="Bob Gregory",
    author_email="bob@codefiend.co.uk",
    description="Unintrusive dependency injection for Python 3.8+",
    long_description=long_description,
    packages=["punq"],
    package_data={"punq": ["CHANGES.md"]},
    include_package_data=True,
    platforms="any",
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)
