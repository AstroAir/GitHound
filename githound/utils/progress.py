"""Advanced progress reporting and cancellation support for GitHound."""

import signal
import threading
import time
from typing import Callable, Optional, Dict, Any

from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, 
    TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
)
from rich.live import Live
from rich.table import Table


class CancellationToken:
    """Thread-safe cancellation token for long-running operations."""
    
    def __init__(self):
        self._cancelled = threading.Event()
        self._lock = threading.Lock()
        self._reason = None
    
    def cancel(self, reason: str = "Operation cancelled"):
        """Cancel the operation with an optional reason."""
        with self._lock:
            self._reason = reason
            self._cancelled.set()
    
    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled.is_set()
    
    @property
    def reason(self) -> Optional[str]:
        """Get the cancellation reason."""
        with self._lock:
            return self._reason
    
    def check_cancelled(self):
        """Raise an exception if cancellation has been requested."""
        if self.is_cancelled:
            raise OperationCancelledException(self.reason or "Operation cancelled")


class OperationCancelledException(Exception):
    """Exception raised when an operation is cancelled."""
    pass


class ProgressManager:
    """Advanced progress manager with multiple task tracking and cancellation support."""
    
    def __init__(self, console: Optional[Console] = None, enable_cancellation: bool = True):
        self.console = console or Console()
        self.enable_cancellation = enable_cancellation
        self.cancellation_token = CancellationToken()
        self._progress = None
        self._tasks = {}
        self._stats = {}
        self._start_time = None
        self._signal_handler_set = False
    
    def __enter__(self):
        self._start_time = time.time()
        
        # Set up signal handler for Ctrl+C
        if self.enable_cancellation and not self._signal_handler_set:
            signal.signal(signal.SIGINT, self._signal_handler)
            self._signal_handler_set = True
        
        # Create progress display
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        
        self._progress.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._progress:
            self._progress.__exit__(exc_type, exc_val, exc_tb)
        
        # Show final statistics
        if self._start_time:
            elapsed = time.time() - self._start_time
            self._show_final_stats(elapsed, exc_type is not None)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C signal."""
        self.console.print("\n[yellow]Cancellation requested... Please wait for graceful shutdown.[/yellow]")
        self.cancellation_token.cancel("User requested cancellation (Ctrl+C)")
    
    def add_task(self, name: str, description: str, total: Optional[int] = None) -> str:
        """Add a new progress task."""
        if not self._progress:
            raise RuntimeError("ProgressManager not initialized. Use within 'with' statement.")
        
        task_id = self._progress.add_task(description, total=total or 100)
        self._tasks[name] = task_id
        self._stats[name] = {
            'started': time.time(),
            'completed': 0,
            'total': total or 100,
            'description': description
        }
        return name
    
    def update_task(self, name: str, advance: Optional[int] = None, 
                   completed: Optional[int] = None, description: Optional[str] = None):
        """Update a progress task."""
        if name not in self._tasks:
            raise ValueError(f"Task '{name}' not found")
        
        # Check for cancellation
        self.cancellation_token.check_cancelled()
        
        task_id = self._tasks[name]
        
        if advance is not None:
            self._progress.advance(task_id, advance)
            self._stats[name]['completed'] += advance
        
        if completed is not None:
            self._progress.update(task_id, completed=completed)
            self._stats[name]['completed'] = completed
        
        if description is not None:
            self._progress.update(task_id, description=description)
            self._stats[name]['description'] = description
    
    def complete_task(self, name: str, description: Optional[str] = None):
        """Mark a task as completed."""
        if name not in self._tasks:
            return
        
        task_id = self._tasks[name]
        total = self._stats[name]['total']
        
        self._progress.update(
            task_id, 
            completed=total, 
            description=description or f"✓ {self._stats[name]['description']}"
        )
        self._stats[name]['completed'] = total
    
    def get_progress_callback(self, task_name: str) -> Callable[[str, float], None]:
        """Get a progress callback function for a specific task."""
        def callback(description: str, progress: float):
            if task_name in self._tasks:
                total = self._stats[task_name]['total']
                completed = int(progress * total)
                self.update_task(task_name, completed=completed, description=description)
        
        return callback
    
    def _show_final_stats(self, elapsed_time: float, had_error: bool):
        """Show final statistics after completion."""
        if not self._stats:
            return
        
        # Create summary table
        table = Table(title="Search Summary", show_header=True, header_style="bold magenta")
        table.add_column("Task", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="yellow")
        table.add_column("Time", style="blue")
        
        for name, stats in self._stats.items():
            task_elapsed = time.time() - stats['started']
            progress_pct = (stats['completed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            
            status = "❌ Error" if had_error else ("⚠️ Cancelled" if self.cancellation_token.is_cancelled else "✅ Complete")
            progress_str = f"{stats['completed']}/{stats['total']} ({progress_pct:.1f}%)"
            time_str = f"{task_elapsed:.1f}s"
            
            table.add_row(name, status, progress_str, time_str)
        
        # Add total row
        table.add_row(
            "[bold]Total[/bold]", 
            "[bold]—[/bold]", 
            "[bold]—[/bold]", 
            f"[bold]{elapsed_time:.1f}s[/bold]"
        )
        
        self.console.print("\n")
        self.console.print(table)
        
        if self.cancellation_token.is_cancelled:
            self.console.print(f"\n[yellow]Operation cancelled: {self.cancellation_token.reason}[/yellow]")
        elif had_error:
            self.console.print("\n[red]Operation completed with errors.[/red]")
        else:
            self.console.print("\n[green]Operation completed successfully![/green]")


class SimpleProgressReporter:
    """Simple progress reporter for basic use cases."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._last_update = 0
        self._update_interval = 0.5  # Update every 500ms
    
    def report(self, message: str, progress: Optional[float] = None):
        """Report progress with optional percentage."""
        current_time = time.time()
        
        # Throttle updates to avoid spam
        if current_time - self._last_update < self._update_interval:
            return
        
        self._last_update = current_time
        
        if progress is not None:
            progress_pct = progress * 100
            self.console.print(f"[cyan]{message}[/cyan] [yellow]({progress_pct:.1f}%)[/yellow]")
        else:
            self.console.print(f"[cyan]{message}[/cyan]")


def create_progress_callback(
    progress_manager: ProgressManager, 
    task_name: str
) -> Callable[[str, float], None]:
    """Create a progress callback for use with search operations."""
    return progress_manager.get_progress_callback(task_name)
