# Star Ray

star-ray is an experimental multi-agent simulation platform that supports the development of AI agents and their environments.

### Why Star? 

**Star** stands for: **S**imulation **T**estbed for **A**gent **R**esearch, this platform has a long history of revisions (see e.g. [pystarworlds](https://github.com/dicelab-rhul/pystarworlds)), and was originally based on the [GOLEM](https://www.cs.rhul.ac.uk/home/kostas/pubs/debs09.pdf) framework, it is conceptually similar to the previous instantiations but makes many practical improvements over previous iterations.

### Why Ray?

_Ray is a unified framework for scaling AI and Python applications. Ray consists of a core distributed runtime and a set of AI libraries for simplifying [Machine Learning] compute._

Developing robust distributed systems is **hard**, rather than reinvent the wheel we decided to make use of Ray - a powerful distributed systems package that is widely used in the AI/ML community. It has a convenient API which is abstract enough to fit well with existing GOLEM concepts. 

### What does Star-Ray do? 

Star-ray provides abstractions that supports developers to quickly develop software (AI) agents and multi-agent simulations allowing you to focus on some of the more interesting aspects of AI agents such a their individual behaviour or group interaction.

Star-ray implements: **sensors**, **actuators**, an event system (**actions** and **observations**), and **environment** which can be extended to ease development. These provide the backbone to your simulation and abstract away from the complexities of parallel execution and distribution.

## Getting Started

### Documentation

Official documentation is coming soon, if you wish to get started with star-ray before this check out the following package(s) for inspiration:
- [icua2](https://github.com/dicelab-rhul/icua2)

or contact the owners of this repo.
