from __future__ import annotations

import abc
from logging import Logger
from typing import TYPE_CHECKING, Optional, Union, get_args

from pydantic import BaseModel, Field

from autogpts.autogpt.autogpt.core.configuration import AFAASModel
from autogpts.autogpt.autogpt.core.agents import AbstractAgent

# from autogpts.autogpt.autogpt.core.tools.schema import ToolResult
logger = Logger(name=__name__)

class BaseTask(AFAASModel):
    """
    Model representing a task.

    Attributes:
    - responsible_agent_id: ID of the responsible agent (default is None).
    - objective: Objective of the task.
    - type: Type of the task (corresponds to TaskType, but due to certain issues, it's defined as str).
    - priority: Priority of the task.
    - ready_criteria: List of criteria to consider the task as ready.
    - acceptance_criteria: List of criteria to accept the task.
    - context: Context of the task (default is a new TaskContext).

    Example:
        >>> task = Task(objective="Write a report", type="write", priority=2, ready_criteria=["Gather info"], acceptance_criteria=["Approved by manager"])
        >>> print(task.objective)
        "Write a report"
    """
    class Config(AFAASModel.Config):
        # This is a list of Field to Exclude during serialization
        default_exclude = set(AFAASModel.Config.default_exclude) |  {
            "subtasks",
            "agent"
            }
        json_encoders = AFAASModel.Config.json_encoders | {
            }
        
    ###
    ### GENERAL properties
    ###
    if TYPE_CHECKING : 
        from autogpts.autogpt.autogpt.core.agents import BaseAgent

    agent : AbstractAgent = Field(exclude=True)
    @property
    def agent_id(self):
        return self.agent.agent_id
    
    task_id: str 

    task_goal: str
    """ The title / Name of the task """

    task_context: Optional[str]
    """ Placeholder : Context given by RAG & other elements """

    long_decription: Optional[str] 
    """ Placeholder : A longer description of the task than `task_goal` """

    ###
    ### Task Management properties
    ###
    task_history: Optional[list[dict]]
    subtasks: list [BaseTask] = []
    acceptance_criteria: Optional[list[str]] = []

    _default_command : str = None
    @classmethod
    def default_command(cls) -> str: 
        if cls._default_command is not None :
            return cls._default_command
        
        try : 
            import autogpts.autogpt.autogpt.core.agents.routing
            cls._default_command = "afaas_routing"
        except :
            cls._default_command= "afaas_make_initial_plan"
                
        return cls._default_command
    
    def dict_memory(self, **kwargs) -> dict:
        d = super().dict(**kwargs)

        # Iterate over each attribute of the dict
        for field, field_info in self.__fields__.items():
            field_value = getattr(self, field)

            if field_value is not None:
                field_type = field_info.outer_type_

                # Direct check for BaseTask instances
                if isinstance(field_value, BaseTask):
                    d[field] = field_value.task_id

                # Check for lists of BaseTask instances
                if isinstance(field_value, list) and issubclass(get_args(field_type)[0], BaseTask):
                    # Replace the list of BaseTask instances with a list of their task_ids
                    d[field] = [v.task_id for v in field_value]

        return self._apply_custom_encoders(data = d)
        
        
    def add_tasks(self, tasks : list["BaseTask"], agent : BaseAgent, position: int = None):
        if position is not None:
            for task in tasks:
                self.subtasks.insert(task, position)
                task.create_in_db(task = task, agent = self.agent)
        else:
            for task in tasks:
                self.subtasks.append(task)
                task.create_in_db(task = task, agent = self.agent)

        self.agent.plan.register_tasks(tasks = tasks)


    def __getitem__(self, index: Union[int, str]):
        """
        Get a task from the plan by index or slice notation. This method is an alias for `get_task`.

        Args:
            index (Union[int, str]): The index or slice notation to retrieve a task.

        Returns:
            Task or List [BaseTask]: The task or list of tasks specified by the index or slice.

        Examples:
            >>> plan = Plan([Task("Task 1"), Task("Task 2")])
            >>> plan[0]
            Task(task_goal='Task 1')
            >>> plan[1:]
            [Task(task_goal='Task 2')]

        Raises:
            IndexError: If the index is out of range.
            ValueError: If the index type is invalid.
        """
        return self.get_task_with_index(index)

    def get_task_with_index(self, index: Union[int, str]):
        """
        Get a task from the plan by index or slice notation.

        Args:
            index (Union[int, str]): The index or slice notation to retrieve a task.

        Returns:
            Task or List [BaseTask]: The task or list of tasks specified by the index or slice.

        Examples:
            >>> plan = Plan([Task("Task 1"), Task("Task 2")])
            >>> plan.get_task(0)
            Task(task_goal='Task 1')
            >>> plan.get_task(':')
            [Task(task_goal='Task 1'), Task(task_goal='Task 2')]

        Raises:
            IndexError: If the index is out of range.
            ValueError: If the index type is invalid.
        """
        if isinstance(index, int):
            # Handle positive integers and negative integers
            if -len(self.subtasks) <= index < len(self.subtasks):
                return self.subtasks[index]
            else:
                raise IndexError("Index out of range")
        elif isinstance(index, str) and index.startswith(":") and index[1:].isdigit():
            # Handle notation like ":-1"
            start = 0 if index[1:] == "" else int(index[1:])
            return self.subtasks[start:]
        else:
            raise ValueError("Invalid index type")

    ###
    ### FIXME : To test
    ###
    def remove_task(self, task_id: str):
        logger.error("""FUNCTION NOT WORKING :
                     1. We now manage multiple predecessor
                     2. Tasks should not be deleted but managed by state""")
        # 1. Set all task_predecessors_id to null if they reference the task to be removed
        def clear_predecessors(task: BaseTask):
            if task_id in task.task_predecessors_id :
                task.task_predecessors_id.remove(task_id)
            for subtask in task.subtasks or []:
                clear_predecessors(subtask)

        # 2. Remove leaves with status "DONE" if ALL their siblings have this status
        def should_remove_siblings(
            task: BaseTask, task_parent: Optional [BaseTask] = None
        ) -> bool:
            # If it's a leaf and has a parent
            if not task.subtasks and task_parent:
                all_done = all(st.status == "DONE" for st in task_parent.subtasks)
                if all_done:
                    # Delete the Task objects
                    for st in task_parent.subtasks:
                        del st
                    task_parent.subtasks = None  # or []
                return all_done
            # elif task.subtasks:
            #     for st in task.subtasks:
            #         should_remove_siblings(st, task)
            return False

        for task in self.subtasks:
            should_remove_siblings(task)
            clear_predecessors(task)

    def get_ready_leaf_tasks(self) -> list [BaseTask]:
        """
        Get tasks that have status "READY", no subtasks, and no task_predecessors_id.

        Returns:
            List [BaseTask]: A list of tasks meeting the specified criteria.
        """
        logger.notice(
            "Deprecated : Recommended functions are:\n" +
            "- Plan.get_ready_tasks()\n" +
            "- Task.get_first_ready_task()\n" +
            "- Plan.get_next_task()\n"
        )
        ready_tasks = []

        def check_task(task: BaseTask):
            if (
                task.status == "READY"
                and not task.subtasks
                and not task.task_predecessors_id
            ):
                ready_tasks.append(task)

            # Check subtasks recursively
            for subtask in task.subtasks or []:
                check_task(subtask)

        # Start checking from the root tasks in the plan
        for task in self.subtasks:
            check_task(task)

        return ready_tasks

    def get_first_ready_task(self) -> Optional [BaseTask]:
        """
        Get the first task that has status "READY", no subtasks, and no task_predecessors_id.

        Returns:
            Task or None: The first task meeting the specified criteria or None if no such task is found.
        """

        def check_task(task: BaseTask) -> Optional [BaseTask]:
            if (
                task.status == "READY"
                and not task.subtasks
                and not task.task_predecessors_id
            ):
                return task

            # Check subtasks recursively
            for subtask in task.subtasks or []:
                found_task = check_task(subtask)
                if (
                    found_task
                ):  # If a task is found in the subtasks, return it immediately
                    return found_task
            return None

        # Start checking from the root tasks in the plan
        for task in self.subtasks:
            found_task = check_task(task)
            if found_task:
                return found_task

        return None
    
    @staticmethod
    def info_parse_task(task: BaseTask) -> str:
        from .task import Task
        parsed_response = f"Agent Plan:\n"
        task : Task
        for i, task in enumerate(task.subtasks):
            parsed_response += f"{i+1}. {task.task_id} - {task.task_goal}\n"
            parsed_response += f"Description {task.long_decription}\n"
            # parsed_response += f"Task type: {task.type}  "
            # parsed_response += f"Priority: {task.priority}\n"
            parsed_response += f"Predecessors:\n"
            for j, predecessor in enumerate(task.task_predecessors):
                 parsed_response += f"    {j+1}. {predecessor}\n"
            parsed_response += f"Successors:\n"
            for j, succesors in enumerate(task.task_successors):
                 parsed_response += f"    {j+1}. {succesors}\n"
            parsed_response += f"Acceptance Criteria:\n"
            for j, criteria in enumerate(task.acceptance_criteria):
                parsed_response += f"    {j+1}. {criteria}\n"
            parsed_response += "\n"

        return parsed_response
    
    def dump(self, depth=0) -> dict:
        if depth < 0:
            raise ValueError("Depth must be a non-negative integer.")

        # Initialize the return dictionary
        return_dict = self.dict()

        # Recursively process subtasks up to the specified depth
        if depth > 0 and self.subtasks:
            return_dict["subtasks"] = [
                subtask.dump(depth=depth - 1) for subtask in self.subtasks
            ]

        return return_dict

    def find_task(self, task_id: str):
        """
        Recursively searches for a task with the given task_id in the tree of tasks.
        """
        logger.warning("Deprecated : Recommended function is Plan.get_task()")
        # Check current task
        if self.task_id == task_id:
            return self

        # If there are subtasks, recursively check them
        if self.subtasks:
            for subtask in self.subtasks:
                found_task = subtask.find_task(task_id = task_id)
                if found_task:
                    return found_task
        return None

    def find_task_path_with_id(self, search_task_id: str):
        """
        Recursively searches for a task with the given task_id and its parent tasks.
        Returns the parent task and all child tasks on the path to the desired task.
        """

        logger.warning("Deprecated : Recommended function is Task.find_task_path()")

        if self.task_id == search_task_id:
            return self

        if self.subtasks:
            for subtask in self.subtasks:
                found_task = subtask.find_task_path_with_id(search_task_id)
                if found_task:
                    return [self] + [found_task]
        return None


    #
    @abc.abstractmethod
    def create_in_db(self, agent: BaseAgent) :
        ...


# Need to resolve the circular dependency between Task and TaskContext once both models are defined.
BaseTask.update_forward_refs()