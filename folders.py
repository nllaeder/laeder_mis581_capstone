import os

def generate_obsidian_structure(base_dir="CapstoneProject"):
    """
    Generates an Obsidian-compatible directory structure with Markdown files.

    Args:
        base_dir (str): The name of the main project directory.
    """

    # Create the base directory
    os.makedirs(base_dir, exist_ok=True)

    # Helper function to create directories and files
    def create_dir_and_files(path, files):
        os.makedirs(path, exist_ok=True)
        for file in files:
            with open(os.path.join(path, file), "w") as f:
                pass  # Create empty file

    # I. Project Overview
    create_dir_and_files(
        os.path.join(base_dir, "Project_Overview"),
        [
            "Project_Goals_and_Objectives.md",
            "Scope.md",
            "Timeline_and_Milestones.md",
            "Stakeholders.md",
        ],
    )

    # II. Requirements and Specifications
    create_dir_and_files(
        os.path.join(base_dir, "Requirements_and_Specifications"),
        [
            "Peer_1_Requirements.md",
            "Peer_2_Requirements.md",
            "Data_Source_Specifications.md",
            "Data_Warehouse_Requirements.md",
            "LLM_and_Podcast_Requirements.md",
        ],
    )

    # III. System Design
    create_dir_and_files(
        os.path.join(base_dir, "System_Design"),
        [
            "Architecture_Diagram_ELT.md",
            "Data_Flow_Diagrams.md",
            "Data_Schema.md",
            "ETL_Process_Design.md",
        ],
    )

    # IV. Implementation
    create_dir_and_files(
        os.path.join(base_dir, "Implementation"),
        [
            "Environment_Setup.md",
            "ETL_Script_Development.md",
            "LLM_Integration.md",
            "Podcast_Generation.md",
            "Deployment.md",
        ],
    )

    # V. Testing and Evaluation
    create_dir_and_files(
        os.path.join(base_dir, "Testing_and_Evaluation"),
        [
            "ETL_Testing.md",
            "LLM_Output_Evaluation.md",
            "System_Usability.md",
        ],
    )

    # VI. Project Deliverables
    create_dir_and_files(
        os.path.join(base_dir, "Project_Deliverables"),
        [
            "Data_Warehouse.md",
            "ETL_Scripts.md",
            "AI_Generated_Podcast.md",
            "Documentation.md",
            "Final_Report_and_Presentation.md",
        ],
    )

    # VII. Appendix
    create_dir_and_files(base_dir, ["Appendix.md"])

if __name__ == "__main__":
    generate_obsidian_structure("CapstoneProject")  # You can change the main directory name here
    print("Obsidian structure generated successfully!")