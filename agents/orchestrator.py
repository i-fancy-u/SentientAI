# agents/orchestrator.py (MODIFIED AGAIN for async input fix)
import copy
import asyncio # Keep this import

from typing import Dict, Any # Ensure Dict and Any are imported
from .diagnostic_state import DiagnosticState
from .planner_agent import PlannerAgent
from .executor_agent import ExecutorAgent
from .scada_agent import ScadaAgent
from .manual_agent import ManualAgent
from .replan_agent import ReplanAgent
from .synthesizer_agent import SynthesizerAgent

class Orchestrator:
    """
    Orchestrator: Manages the flow of the multi-agent diagnostic system.
    It instantiates and coordinates the Planner, Executor, Replan, Scada,
    Manual, and Synthesizer Agents, updating a shared DiagnosticState.
    Now includes Human-in-the-Loop for plan review/approval.
    """
    def __init__(self):
        self.name = "Orchestrator"
        print(f"🚀 {self.name}: Initializing agents...")

        # Instantiate specialized tool agents first
        self.scada_agent = ScadaAgent()
        self.manual_agent = ManualAgent()

        # Instantiate core agents, injecting dependencies where needed
        self.planner_agent = PlannerAgent()
        # ExecutorAgent needs access to the specialized tool agents
        self.executor_agent = ExecutorAgent(
            scada_agent=self.scada_agent,
            manual_agent=self.manual_agent
        )
        self.replan_agent = ReplanAgent()
        self.synthesizer_agent = SynthesizerAgent()

        print(f"✅ {self.name}: All agents initialized.")

    async def _human_in_the_loop_review(self, state: DiagnosticState) -> Dict[str, Any]:
        """
        Pauses the workflow for human review and input.
        Returns a dictionary indicating how to proceed.
        """
        print("\n--- HUMAN IN THE LOOP: Review Required ---")
        print("Current State Overview:")
        print(f"  User Query: {state['input']}")
        print(f"  Completed Steps ({len(state['past_steps'])}):")
        if state['past_steps']:
            for i, (step, result) in enumerate(state['past_steps'], 1):
                print(f"    {i}. {step}")
                # Ensure result is a string before slicing
                result_preview = str(result)[:100] + "..." if result else "No result"
                print(f"       Result Preview: {result_preview}")
        else:
            print("    No steps completed yet.")

        print(f"  Next Planned Steps ({len(state['plan'])}):")
        if state['plan']:
            for i, step in enumerate(state['plan'], 1):
                print(f"    {i}. {step}")
        else:
            print("    No new steps proposed by Replan Agent.")

        print("\nOptions:")
        print("  'c' / 'continue': Proceed with the current plan.")
        print("  's' / 'synthesize': Force synthesis of a final answer now.")
        print("  'e' / 'edit': Manually edit the plan (experimental).")
        print("  'q' / 'quit': Abort the workflow.")

        while True:
            # AWAIT the result of asyncio.to_thread
            choice_raw = await asyncio.to_thread(input, "Your decision (c/s/e/q): ")
            choice = choice_raw.strip().lower() # Now strip() is called on the string result

            if choice in ['c', 'continue']:
                return {"action": "continue"}
            elif choice in ['s', 'synthesize']:
                return {"action": "synthesize"}
            elif choice in ['e', 'edit']:
                print("\n--- MANUAL PLAN EDIT ---")
                new_plan_str_raw = await asyncio.to_thread(input, "Enter new plan steps (comma-separated, e.g., 'SCADA: Get X, MANUAL: Search Y'): ")
                new_plan_str = new_plan_str_raw.strip()
                new_plan = [step.strip() for step in new_plan_str.split(',') if step.strip()]
                return {"action": "edit", "new_plan": new_plan}
            elif choice in ['q', 'quit']:
                return {"action": "quit"}
            else:
                print("Invalid choice. Please enter 'c', 's', 'e', or 'q'.")

    async def run_diagnostic_workflow(self, initial_query: str) -> str:
        """
        Runs the complete diagnostic workflow from planning to synthesis.
        """
        # Initialize the shared state
        state: DiagnosticState = {
            "input": initial_query,
            "plan": [],
            "past_steps": [],
            "response": "",
            "ready_for_synthesis": False
        }
        print(f"\n--- Starting Diagnostic Workflow for: '{initial_query}' ---")

        # 1. Planner Step
        print("\n--- Planner Step ---")
        planner_output = self.planner_agent.create_plan(state)
        state["plan"] = planner_output.get("plan", [])
        if not state["plan"]:
            state["response"] = "The planner could not create a valid plan. Please try a different query."
            print(f"🛑 {self.name}: Planner failed to create a plan. Ending workflow.")
            return state["response"]

        # Main execution loop
        max_iterations = 5 # Safety break to prevent infinite loops
        current_iteration = 0
        while not state["ready_for_synthesis"] and not state["response"] and current_iteration < max_iterations:
            current_iteration += 1
            print(f"\n--- Execution Loop Iteration {current_iteration} ---")

            if not state["plan"]:
                print(f"⚠️ {self.name}: Plan is empty, but not ready for synthesis. Forcing replan decision.")
                state["ready_for_synthesis"] = True

            if state["plan"]:
                # 2. Executor Step (Execute the first step in the plan)
                print("--- Executor Step ---")
                executor_output = self.executor_agent.execute_step(state)
                state["past_steps"] = state["past_steps"] + executor_output.get("past_steps", [])

                # Remove the executed step from the plan
                state["plan"] = state["plan"][1:]
                print(f"📋 Remaining plan steps: {state['plan']}")

            # 3. Replan Step
            print("\n--- Replan Step ---")
            replan_output = self.replan_agent.decide_next_action(state)

            # Update state based on replan agent's decision
            if "ready_for_synthesis" in replan_output:
                state["ready_for_synthesis"] = replan_output["ready_for_synthesis"]
            if "response" in replan_output:
                state["response"] = replan_output["response"]
            if "plan" in replan_output and replan_output["plan"]:
                state["plan"] = state["plan"] + replan_output["plan"]
                print(f"📋 Replan Agent added {len(replan_output['plan'])} new steps. Total plan: {state['plan']}")
            elif "plan" in replan_output and not replan_output["plan"] and not state["ready_for_synthesis"] and not state["response"]:
                print(f"⚠️ {self.name}: Replan Agent returned empty plan without synthesis signal. Forcing synthesis.")
                state["ready_for_synthesis"] = True

            # --- HUMAN IN THE LOOP INTEGRATION ---
            if not state["ready_for_synthesis"] and not state["response"]: # Only ask human if not already ending
                human_decision = await self._human_in_the_loop_review(state)

                if human_decision["action"] == "quit":
                    state["response"] = "Workflow aborted by human."
                    print(f"🛑 {self.name}: Workflow aborted by human. Ending.")
                    break # Exit the main loop
                elif human_decision["action"] == "synthesize":
                    state["ready_for_synthesis"] = True
                    print(f"➡️ {self.name}: Human forced synthesis.")
                elif human_decision["action"] == "edit":
                    state["plan"] = human_decision["new_plan"]
                    print(f"✏️ {self.name}: Human edited plan to: {state['plan']}")
                    current_iteration = 0 # Allow more iterations after human edit
                # If "continue", loop proceeds as normal

        # 4. Synthesizer Step (if ready)
        if state["ready_for_synthesis"] and not state["response"]:
            print("\n--- Synthesizer Step ---")
            synthesizer_output = self.synthesizer_agent.synthesize_response(state)
            state["response"] = synthesizer_output.get("response", "An error occurred during final synthesis.")
            print(f"✅ {self.name}: Final response synthesized.")
        elif not state["response"]:
            state["response"] = "The diagnostic process completed without a final synthesized response. Please review the past steps for information."
            print(f"🛑 {self.name}: Workflow ended without synthesis or response (max iterations reached or unexpected state).")

        print("\n--- Diagnostic Workflow Completed ---")
        return state["response"]