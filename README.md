# Dynamic Flag CTFd Framework

This project provides a framework for creating dynamic challenges in CTFd, a popular platform for hosting Capture The Flag (CTF) competitions.

## What are Dynamic Challenges?

Despite the name, the challenges themself are not dynamic at all. Instead, what this plugin tries to achieve is to unify the flag management that was before split into CTFd and the machine containing the challenges, so that the process of creating the challenge in the machine and making it appear in CTFd with all of the configurations necessary can be abstracted and added to a single pipeline (e.g. [pipeline-prod.yml](https://github.com/FCUP-MSI/LEIC-FSI-desafios/blob/main/.github/workflows/pipeline-prod.yml)).

## Overview

This framework allows for the dynamic management of flags in CTFd challenges, including updating flags, restarting containers, and checking flags. You can think of this framework as a centralized controller that deals with the logic and integration of the various components.

This framework deals with changing the flag whenever a team gets a new solve on a particular challenge while keeping consistency across the various components. This is particularly useful for Capture the Flag competitions where you wan't to prevent flag sharing.

- **Note:** Even though this seems ideal, it does not fully prevent plagium / flag-sharing, since a team can always solve the challenge again and share those new flags to other teams. To deal with this more complex mechanisms need to be implemented (e.g. some of them have been implemented in [LEIC-new-FSI-infra](https://github.com/FCUP-MSI/LEIC-new-FSI-infra)). 

## Labels

The following Docker labels are used to configure dynamic challenges:

* `dynamic-label=true` : enable dynamic challenge
* `challenge-name`: name of the challenge
* `flag-localization` : localization of the file where the flag is
* `flag-script` : script that it's called with the flag to update it
* `restart-after-flag`


## Environment Variables

The following environment variables need to be set for the framework to function properly:

* `CTFD_URL`: CTFd API endpoint, ending with `/api/v1`.
* `TOKEN`: Authentication token for accessing the CTFd API.
* `DEBUG`: Set to enable debug logging (optional).

## Usage

To test the framework, you can run a Docker container with the appropriate labels:

```sh
docker run --rm -it -l "dynamic-label=true" alpine /bin/bash
```

You can also see an example of how it can be used in production in [this](https://github.com/FCUP-MSI/LEIC-new-FSI-infra/blob/main/docker-compose.yml) docker-compose.