import os
import sys
import asyncio
import signal
from dotenv import load_dotenv
from assistant.main import Assistant
from interfaces.telegram.bot import TelegramBot

async def check_tasks(assistant: Assistant, bot: TelegramBot):
    """Background task to check for due tasks periodically"""
    try:
        while True:
            try:
                assistant.process_due_tasks(
                    message_callback=bot.broadcast_message,
                    tool_callback=bot.send_tool_notification
                )
            except Exception as e:
                print(f"Error processing tasks: {e}")
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        print("Task checker cancelled")

async def shutdown(bot, task_checker):
    """Cleanup tasks tied to the service's shutdown."""
    print("Shutting down...")
    
    if not task_checker.cancelled():
        task_checker.cancel()
        try:
            await task_checker
        except asyncio.CancelledError:
            pass
    
    await bot.stop()
    
    remaining_tasks = [t for t in asyncio.all_tasks() 
                      if t is not asyncio.current_task() and not t.cancelled()]
    if remaining_tasks:
        print(f"Cancelling {len(remaining_tasks)} remaining tasks")
        for task in remaining_tasks:
            task.cancel()
        await asyncio.gather(*remaining_tasks, return_exceptions=True)

def handle_exception(loop, context):
    """Handle exceptions in the event loop."""
    msg = context.get("exception", context["message"])
    print(f"Error in async loop: {msg}")

async def main():
    load_dotenv()
    
    assistant = Assistant()
    bot = TelegramBot(assistant)
    
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_exception)
    
    task_checker = asyncio.create_task(check_tasks(assistant, bot))
    
    try:
        await bot.start()
        
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        print("Main task cancelled")
    except KeyboardInterrupt:
        print("Received keyboard interrupt...")
    finally:
        await shutdown(bot, task_checker)

def run():
    """Run the application with proper setup and error handling"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Cleanup complete, exiting...")

if __name__ == "__main__":
    run()
