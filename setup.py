import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bookstore",
    version="0.0.1",
    author="DaSE-DBMS",
    author_email="DaSE-DBMS@DaSE-DBMS.com",
    description="Buy Books Online",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DaSE-DBMS/bookstore.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        'flask>=2.0.0',
        'sqlalchemy>=1.4.0',
        'pymysql>=1.0.0',
        'bcrypt>=4.0.0',
        'pyjwt>=2.0.0',
        'python-dotenv>=0.19.0',
    ],
)
