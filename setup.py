import setuptools

setuptools.setup(
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU License",
        "Operating System :: POSIX :: Linux",
    ],
    name="RotaTimetable",
    version="0.0.1",
    author="Arif Er",
    description="Package to manage turnouts every shift",
    include_package_data=True,
    # install_requires=install_requires,
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/arifer612/RotaTimetable",
    packages=setuptools.find_packages(),
    package_data={
    },
    python_requires=">=3.6",
)