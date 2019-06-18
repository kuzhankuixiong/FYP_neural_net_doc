import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="brian2docs",
    version="1.0.0",
    author="Zeqian Cao",
    author_email="1733884649@qq.com",
    description="A package generate pdf document for brian2 neural network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kuzhankuixiong/FYP_neural_net_doc",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
