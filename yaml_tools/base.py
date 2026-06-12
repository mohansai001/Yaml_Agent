from agent_framework import tool #type: ignore
from typing import Annotated
from pydantic import Field
from agent_framework import tool #type: ignore
from typing import Annotated
from pydantic import Field
import requests
import yaml
import base64
# from github import Github, Auth #type: ignore
from openai import OpenAI, AzureOpenAI  #type: ignore
import asyncio
import os
from utils.config import AZURE_AI_API_KEY,github_token,azure_config,REPO_OWNER,TERRAFORM_MODULES_REPO
from utils.github_client import get_github_client
from adapters.github.git_write import set_github_secret
from adapters.github.git_read import wait_for_latest_workflow,github_read_contents
from utils.prompt_manager_v2 import GeneratorPrompt, ToolDescriptionPrompt
import json
from github import Github #type: ignore
from adapters.github.git_read import get_artifact_name_from_run
# auth = Auth.Token(github_token)
# g = get_github_client() 
rg = get_github_client(github_token)

from utils.clientConnection import get_client
from .content_generator import create_yaml_scripts
from utils.logger import get_logger
logger = get_logger(__name__)

# client = get_client(model=Content_generator_model_config.model, endpoint=Content_generator_model_config.AI_content_endpoint,api_version = "2024-05-01-preview")

def github_read_yaml_library(FILE_PATH="file-paths-registry.yml", g: Github = rg):
    
    REPO_NAME = "Yaml-Templates"
    repo = rg.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    file = repo.get_contents(f"{FILE_PATH}")
    return yaml.safe_load(file.decoded_content.decode())

def get_cicd_paths(config, tool, language=None, target=None):
    result = {}

    tool_data = config.get("cicd_tools", {}).get(tool, {})

    if not tool_data:
        raise ValueError(f"Invalid tool: {tool}")

    # Extract CI template
    if language:
        ci_templates = tool_data.get("ci_templates", {})
        ci_path = ci_templates.get(language)

        if not ci_path:
            raise ValueError(f"CI template not found for language: {language}")

        result["ci"] = ci_path

    # Extract CD template
    if target:
        cd_templates = tool_data.get("cd_templates", {})
        cd_path = cd_templates.get(target)

        if not cd_path:
            raise ValueError(f"CD template not found for target: {target}")

        result["cd"] = cd_path

    return result
from adapters.github.git_write import commit_files as github_commit_files
from github import Github #type: ignore

def github_push_files(files_to_push, repo_name, commit_message, branch="main", g: Github =rg):
    # repo = g.get_repo(f"{REPO_OWNER}/{repo_name}")
    print("In the github_push_files function\n")
    results = []
    for file_path, file_content in files_to_push.items():
        try:
            # Try to get existing file
            # existing_file = repo.get_contents(file_path, ref=branch)
            # Update existing file
            response = github_commit_files(
                g=g,
                repo=repo_name,
                file_path=file_path,
                commit_message=commit_message,
                branch=branch,
                content=file_content
            )
            results.append(response)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    return results

import time

@tool(name="CI_builder", description=str(ToolDescriptionPrompt("ci-builder-tool-description")), approval_mode="never_require")
async def CI_Builder(tool: Annotated[str, Field(description="The CI tool to used for the application the tool name should be in lower case without spaces, the sapce should be replaces with '_' .Example : github_actions")],
                     techstack: Annotated[str, Field(description="The tech stack that is used to develop the application and in the repository, The tech stack name should be in lower case. Example : python")],
                     repo_name: Annotated[str, Field(description="The repository name")],
                     branch_name: Annotated[str, Field(description="The branch name")]):
    # Assuming Tech stack, tool, Repository name and Framework comes from the orchestrator agent
    try:
        logger.info("[CI_Builder] Tool called.")
        # print("[CI_Builder] Tool called.")
        logger.info(f"[CI_Builder] Input parameters - Tech Stack: {techstack}, Tool: {tool}, Repo Name: {repo_name}")
        # print(f"[CI_Builder] Input parameters - Tech Stack: {techstack}, Tool: {tool}, Repo Name: {repo_name}")
        # print(f"Tech Stack: {techstack}")

        logger.info("[CI_Builder] Reading YAML library for CI template paths...")
        # print("[CI_Builder] Reading YAML library for CI template paths...")
        yaml_data = github_read_yaml_library()
        logger.info(f"[CI_Builder] YAML data keys: {list(yaml_data.keys())}")
        # print(f"[CI_Builder] YAML data keys: {list(yaml_data.keys())}")

        paths = get_cicd_paths(yaml_data, tool, techstack)
        logger.info(f"[CI_Builder] CI template path: {paths.get('ci')}")
        # print(f"[CI_Builder] CI template path: {paths.get('ci')}")

        ci_template = github_read_yaml_library(paths["ci"])
        logger.info("[CI_Builder] Loaded CI template from YAML library.")
        # print("[CI_Builder] Loaded CI template from YAML library.")

        logger.info("[CI_Builder] Preparing instructions for CI pipeline generation.")
        # print("[CI_Builder] Preparing instructions for CI pipeline generation.")
        prompt = GeneratorPrompt("ci-builder-generator")
        instructions = prompt.render(repo_name=repo_name, branch_name=branch_name, ci_template=ci_template)
        # print("Instructions for CI pipeline generation:\n", instructions)

        logger.info("[CI_Builder] Generating CI pipeline script using content generator...")
        # print("[CI_Builder] Generating CI pipeline script using content generator...")
        status,ci_script,message = create_yaml_scripts(instructions)

        # ci_repo_name = "Workflow-files"  # Make ci_repo_name dynamic while deploying.....
        
        # print(f"[CI_Builder] Pushing CI Pipeline script into the repository: {ci_repo_name}")
        # if status:
        #     logger.info(f"[CI_Builder] Pushing CI Pipeline script into the repository: {repo_name}")
        #     result = github_push_files(
        #         {f".github/workflows/{techstack}-ci.yml": ci_script},
        #         f"{repo_name}",
        #         "Pushed by hari",
        #         branch_name,
        #         g = get_github_client(hari_github_token)
        #     )
        #     logger.info(f"[CI_Builder] CI push result: {result}")
        #     logger.info(f"[CI_Builder] Waiting for CI workflow to initialize...")
        #     await asyncio.sleep(10)
        #     workflow_status=wait_for_latest_workflow(repo_name=repo_name,branch=branch_name, workflow_file_name=f"{techstack}-ci.yml")
        #     if workflow_status==True:
        #         art_name, workflow_name = get_artifact_name_from_run(repo_name=repo_name, workflow_file_name=f"{techstack}-ci.yml", branch=branch_name)
        #         logger.info(f"[CI_Builder] Workflow status: {workflow_status}")
        #     else:
        #         logger.error(f"[CI_Builder] Workflow failed or timed out")
        #         return f"Workflow failed or timed out"
        #     # print(f"[CD_Builder] CD push result: {result}")
        return {"TASK COMPLETED" : ci_script}
        #             # "Artifact_name" : art_name,
        #             # "Workflow_name": workflow_name,
        #             # "ci_filename": f"{techstack}-ci.yml"}
        #     # print(f"[CI_Builder] CI push result: {result}")
        # else:
        #     logger.info(f"[CI_Builder] CI script generation failed.{message}")
        #     return{
        #         "Error": message
        #     }
    except Exception as e:
            logger.error(f"[CI_Builder] Error occurred while creating CI pipeline: {e}", exc_info=True)
            # print(f"[CI_Builder] Error occurred while creating CI pipeline: {e}")
            return {
                "Error": str(e)
            }

from utils.config import hari_github_token
from adapters.github.git_read import get_cd_run_metadata
@tool(name="CD_builder", description=str(ToolDescriptionPrompt("cd-builder-tool-description")), approval_mode="never_require")
async def CD_Builder(target: Annotated[str, Field(description="The target environment for the CD pipeline")],
                     techstack: Annotated[str, Field(description="The tech stack that is used to develop the application and in the repo")],
                     repo_name: Annotated[str, Field(description="The repository name")],
                     resource_group_name: Annotated[str, Field(description="The resource group name to be used for the CD pipeline")],
                     deploy_target_name: Annotated[str, Field(description="The deployment target name Example: webapp, vm")],
                     tool: Annotated[str, Field(description="The CI tool to use")],
                     branch: Annotated[str, Field(description="The branch name to be used for the CD pipeline")],
                     artifact_name: Annotated[str, Field(description="The artifact name to be used for the CD pipeline")],
                     workflow_name: Annotated[str, Field(description="The workflow name to be used for the CD pipeline")],
                     ci_file_name: Annotated[str, Field(description="The CI file name to be used for the CD pipeline")]):
    # Assuming Tech stack, tool, Repository name and Framework comes from the orchestrator agent
    try:
        g = get_github_client(hari_github_token)
        logger.info("[CD_Builder] Tool called.")
        # print("[CD_Builder] Tool called.")
        logger.info(f"[CD_Builder] Input parameters - Tech Stack: {techstack}, Tool: {tool}, Repo Name: {repo_name}, Target: {target}")
        # print(f"[CD_Builder] Input parameters - Tech Stack: {techstack}, Tool: {tool}, Repo Name: {repo_name}, Target: {target}")

        logger.info("[CD_Builder] Reading YAML library for CD template paths...")
        # print("[CD_Builder] Reading YAML library for CD template paths...")
        yaml_data = github_read_yaml_library()
        # logger.info(f"[CD_Builder] YAML data keys: {list(yaml_data.keys())}")

        paths = get_cicd_paths(yaml_data, tool, target=target)
        logger.info(f"[CD_Builder] CD template path: {paths.get('cd')}")
        # print(f"[CD_Builder] CD template path: {paths.get('cd')}")

        cd_template = github_read_yaml_library(paths["cd"])
        logger.info("[CD_Builder] Loaded CD template from YAML library.")
        # print("[CD_Builder] Loaded CD template from YAML library.")

        logger.info("[CD_Builder] Preparing instructions for CD pipeline generation.")
        # print("[CD_Builder] Preparing instructions for CD pipeline generation.")
        prompt = GeneratorPrompt("cd-builder-generator")
        instructions = prompt.render(repo_name=repo_name, 
                                     cd_template=cd_template, 
                                     artifact_name=artifact_name, 
                                     workflow_name=workflow_name,
                                     ci_filename = ci_file_name,
                                     resource_group_name = resource_group_name,
                                     deployment_target_name = deploy_target_name)

        logger.info("[CD_Builder] Generating CD pipeline script using content generator...")
        # print("[CD_Builder] Generating CD pipeline script using content generator...")
        status,cd_script,message = create_yaml_scripts(instructions)
        # Make the repo dynamic while deploying...
        # cd_repo_name = "Workflow-files"
        if status:
            logger.info(f"[CD_Builder] CD script generation succeeded.")
            logger.info(f"[CD_Builder] Setting up secrets for CD pipeline in the repository: {repo_name}")
            # for key, value in azure_config.items():
            #     await set_github_secret(f"{REPO_OWNER}/{repo_name}", key, value) #type: ignore
            await set_github_secret(f"{repo_name}", "AZURE_CREDENTIALS", json.dumps(azure_config), g=g)

            
            logger.info(f"[CD_Builder] Pushing CD Pipeline script into the repository: {repo_name}")
            # print(f"[CD_Builder] Pushing CD Pipeline script into the repository: {repo_name}")
            result = github_push_files(
                {f".github/workflows/{target}-cd.yml": cd_script},
                f"{repo_name}",
                "Add CD pipeline",
                branch=branch,
                g=g
            )
            logger.info(f"[CD_Builder] CD push result: {result}")
            
            await asyncio.sleep(10)
            logger.info(f"[CD_Builder] Waiting for CI workflow to complete...")
            ci_workflow_status = wait_for_latest_workflow(f"{repo_name}", f"{ci_file_name}", branch=branch)
            logger.info(f"[CD_Builder] CI Workflow status: {ci_workflow_status}")
            logger.info(f"[CD_Builder] Waiting for CD workflow to initialize...")
            await asyncio.sleep(10)
            workflow_status=wait_for_latest_workflow(f"{repo_name}", f"{target}-cd.yml", branch=branch)
            details = get_cd_run_metadata(repo_name=repo_name, workflow_file_name=f"{target}-cd.yml", branch=branch)
            print(details)
            if workflow_status==True:
                logger.info(f"[CD_Builder] Workflow status: {workflow_status}")
            else:
                logger.error(f"[CD_Builder] Workflow failed or timed out")
                return f"Workflow failed or timed out"
            # print(f"[CD_Builder] CD push result: {result}")
            return {"TASK COMPLETED": {cd_script},
                    "Details": details}
        else:
            logger.error(f"[CD_Builder] CD script generation failed.")
            return {
                "ERROR": message
            }
    except Exception as e:
        logger.error(f"[CD_Builder] Error occurred while creating CD pipeline: {e}", exc_info=True)
        # print(f"[CD_Builder] Error occurred while creating CD pipeline: {e}")
        return {
           "ERROR": str(e)
       }


@tool(name="TF_Builder", description=str(ToolDescriptionPrompt("tf-builder-tool-description")), approval_mode="never_require")
async def TF_Builder(cloud_provider: Annotated[str, Field(description="The cloud provider to be used for the infrastructure (e.g., 'azure', 'aws', 'gcp')")],
                     resource_group: Annotated[str, Field(description="The resource group to be used for the infrastructure")],
                     resources: Annotated[str, Field(description="The resources to be provisioned in the infrastructure")],
                     repo_name: Annotated[str, Field(description="The repository name in the lower case")],
                     deploy_target_name: Annotated[str, Field(description="The deployment target resource name Example: webapp,vm")]):
    try:

        logger.info("[TF_Builder] Tool called.")
        # print("[TF_Builder] Tool called.")
        logger.info(f"[TF_Builder] Input parameters - Cloud Provider: {cloud_provider}, Resource Group: {resource_group}, Resources: {resources}, Repo Name: {repo_name}")
        # print(f"[TF_Builder] Input parameters - Cloud Provider: {cloud_provider}, Resource Group: {resource_group}, Resources: {resources}, Repo Name: {repo_name}")
        template_path="yaml-templates/github-actions/cd/terraform-cd.yml"
        tf_yml_template=github_read_contents(template_path, repo_owner=REPO_OWNER, repo_name="Yaml-Templates")
        logger.info("[TF_Builder] Preparing prompt for Terraform YAML generation.")
        print("Azure Secret keys:", list(azure_config.keys()))
        # print("[TF_Builder] Preparing prompt for Terraform YAML generation.")
        prompt = f"You are a senior Devops Platform Engineer. Generate a Terraform pipeline yml for {cloud_provider} with the following details:\n\n"
        prompt += f"Resource Group: {resource_group}\n"
        prompt += f"Resources: {resources}\n"
        prompt += f"Repository: {repo_name}\n"
        prompt += f"for the terraform init, validate, plan and Apply steps, use working directory as './{repo_name}/{deploy_target_name}' Example: for Working directory is ./repo_name/webapp"
        prompt += f"Please use the below secret key names only for handling storing secret key names , AZURE_CREDENTIALS\n"
        prompt += f"The pipeline Output should contain only the YAML content without any explanations or markdown formatting.Use below template as reference.\n {tf_yml_template}"
        prompt += "Do not add env variables directly refer them \n Also the tech stack contains application_stack in the forfat of 'language: python 3.11(ir; language version), mould it to the acceptable syntax"
        # logger.info(f"[TF_Builder] Prompt: {prompt}")
        # print(f"[TF_Builder] Prompt: {prompt}")

        logger.info("[TF_Builder] Generating Terraform pipeline script using content generator...")
        # print("[TF_Builder] Generating Terraform pipeline script using content generator...")

        status,tf_script,message = create_yaml_scripts(prompt)
        if status:
            tf_repo_name = f"{REPO_OWNER}/{TERRAFORM_MODULES_REPO}"
            logger.info(f"[TF_Builder] Setting up secrets for TF pipeline in {tf_repo_name}")
            # for key, value in azure_config.items():
            #    await set_github_secret(f"{tf_repo_name}", key, value)
            await set_github_secret(f"{tf_repo_name}", "AZURE_CREDENTIALS", json.dumps(azure_config))
            logger.info(f"[TF_Builder] Pushing Terraform Pipeline script into the repository: {tf_repo_name}")
            # print(f"[TF_Builder] Pushing Terraform Pipeline script into the repository: {tf_repo_name}")
            result = github_push_files(
                {f".github/workflows/{repo_name}-tf.yml": tf_script},
                tf_repo_name,
                "Added Terraform pipeline",
                "main"
            )
            logger.info(f"[TF_Builder] TF push result: {result}")
            # print(f"[TF_Builder] TF push result: {result}")
            logger.info(f"[TF_Builder] Waiting for terraform workflow to complete...")
            await asyncio.sleep(10)
            workflow_status=wait_for_latest_workflow(f"{tf_repo_name}", f"{repo_name}-tf.yml")
            if workflow_status==True:
                logger.info(f"[TF_Builder] Workflow status: {workflow_status}")
            else:
                logger.error(f"[TF_Builder] Workflow failed or timed out")
                return f"Workflow failed or timed out"

            logger.info("[TF_Builder] TASK COMPLETED")
            # print("[TF_Builder] TASK COMPLETED")
            # print("==================TASK Completed===================")
            return f"TASK COMPLETED: {tf_script}"
        else:
            return{
                "Error": message
            }
    except Exception as e:
        logger.error(f"[TF_Builder] Error occurred while creating Terraform pipeline: {e}", exc_info=True)
        return {
            "Error": str(e)
        }
        # print(f"[TF_Builder] Error occurred while creating Terraform pipeline: {e}")

def yaml_update():
    pass