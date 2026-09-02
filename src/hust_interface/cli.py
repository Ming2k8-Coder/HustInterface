import sys
import os
import asyncio
from typing import Optional, List, Dict, Any
import click
from rich.console import Console
from rich.table import Table

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .config import settings
from .core.session_manager import session_manager
from .auth.manual_auth import ManualAuthenticator
from .auth.direct_http_auth import DirectHttpAuthenticator
from .server import mcp_server


console = Console(safe_box=True)


@click.group()
def cli():
    """HUST Interface - Model Context Protocol (MCP) Server & Crawler CLI."""
    pass


@cli.command(name="run")
@click.option("--transport", "-t", type=click.Choice(["stdio", "sse"]), default="stdio", help="MCP Transport mechanism (default: stdio)")
@click.option("--port", "-p", type=int, default=8000, help="Port for SSE transport")
@click.option("--host", "-h", default="127.0.0.1", help="Host for SSE transport")
def run_server(transport: str, port: int, host: str):
    """Run the HUST Interface MCP Server."""
    if transport == "stdio":
        mcp_server.run(transport="stdio")
    elif transport == "sse":
        console.print(f"[bold green]Starting HUST MCP Server with SSE on {host}:{port}...[/bold green]")
        mcp_server.run(transport="sse")


@cli.command(name="status")
def show_status():
    """Display the current authentication & session status for HUST services."""
    summary = session_manager.get_auth_summary()

    table = Table(title="HUST Interface - Authentication Status", show_header=True, header_style="bold magenta")
    table.add_column("Dich vu", style="bold cyan")
    table.add_column("Trang thai", style="bold")
    table.add_column("MSSV / User", style="green")
    table.add_column("Chi tiet", style="white")

    for svc, info in summary.items():
        if info.get("authenticated"):
            status_text = "[green]OK (Da xac thuc)[/green]"
            student_id = info.get("student_id") or "N/A"
            details = f"Token: {'Het han' if info.get('expired') else 'Hop le'}"
        else:
            status_text = "[red]Chua xac thuc[/red]"
            student_id = "-"
            details = info.get("status", "Chua cau hinh token/cookie")

        table.add_row(svc.upper(), status_text, student_id, details)

    console.print(table)
    console.print(f"[dim]Session cache: {session_manager.storage_path}[/dim]")


@cli.command(name="set-token")
@click.argument("service", type=click.Choice(["ictsv", "ehust", "ctms"]))
@click.argument("token")
@click.option("--student-id", "-id", default=None, help="Mã số sinh viên (tùy chọn)")
def set_token_cmd(service: str, token: str, student_id: str):
    """Set manual auth token or cookie for a service."""
    if service == "ictsv":
        ManualAuthenticator.set_ictsv_token(token)
        console.print("[bold green]✓ Cap nhat Token CTSV thanh cong![/bold green]")
    elif service == "ehust":
        ManualAuthenticator.set_ehust_cookie(token, student_id=student_id)
        console.print("[bold green]✓ Cap nhat Cookie eHUST thanh cong![/bold green]")
    elif service == "ctms":
        ManualAuthenticator.set_ctms_cookie(token, student_id=student_id)
        console.print("[bold green]✓ Cap nhat Cookie CTMS thanh cong![/bold green]")


@cli.command(name="login-ehust")
@click.option("--cookie", "-c", default=None, help="Chuỗi Cookie eHUST từ Chrome đang mở (x-access-token, x-student-portal-token)")
@click.option("--email", "-e", default=lambda: settings.HUST_EMAIL or "", help="Email sinh viên HUST")
@click.option("--password", "-p", default=lambda: settings.HUST_PASSWORD or "", help="Mật khẩu tài khoản")
def login_ehust_cmd(cookie: Optional[str], email: str, password: str):
    """Đăng nhập eHUST hoặc cập nhật Cookie eHUST (Không mở browser)."""
    if cookie:
        ManualAuthenticator.set_ehust_cookie(cookie)
        console.print("[bold green]✓ Đã cập nhật Cookie eHUST thành công vào session cache![/bold green]")
        return

    if not email or not password:
        console.print("[bold cyan]=== HƯỚNG DẪN CẬP NHẬT COOKIE EHUST TỪ TRÌNH DUYỆT ĐANG MỞ ===[/bold cyan]")
        console.print("1. Mở tab [bold yellow]https://e.hust.edu.vn[/bold yellow] trên Chrome đã đăng nhập.")
        console.print("2. Bấm [bold green]F12[/bold green] -> Chuyển sang tab [bold green]Console[/bold green].")
        console.print("3. Dán lệnh sau và Enter: [bold white on black] copy(document.cookie) [/bold white on black]")
        console.print("4. Cookie đã được sao chép. Dán chuỗi cookie vào bên dưới:")
        cookie_input = click.prompt("Nhập Cookie eHUST")
        ManualAuthenticator.set_ehust_cookie(cookie_input)
        console.print("[bold green]✓ Đã cập nhật Cookie eHUST thành công vào session cache![/bold green]")
        return

    console.print(f"[bold cyan]Đang đăng nhập trực tiếp eHUST cho {email}...[/bold cyan]")
    auth = DirectHttpAuthenticator(email=email, password=password)
    success = asyncio.run(auth.login_ehust_http())
    if success:
        console.print("[bold green]✓ Đăng nhập eHUST thành công! Session đã được lưu.[/bold green]")
    else:
        console.print("[bold red]✗ Đăng nhập thất bại. Vui lòng kiểm tra email/mật khẩu hoặc dán Cookie qua: uv run hust-mcp login-ehust[/bold red]")



@cli.command(name="login-ctsv")
@click.option("--token", "-t", default=None, help="TokenCode / Bearer Token từ Chrome đã mở")
def login_ctsv_cmd(token: Optional[str]):
    """Gather / Set CTSV token from open Chrome session."""
    if not token:
        console.print("[bold cyan]=== HƯỚNG DẪN LẤY TOKEN CTSV TỪ CHROME ĐANG MỞ ===[/bold cyan]")
        console.print("1. Mở tab [bold yellow]https://ctsv.hust.edu.vn[/bold yellow] trên Chrome đã đăng nhập.")
        console.print("2. Bấm [bold green]F12[/bold green] -> Chuyển sang tab [bold green]Console[/bold green].")
        console.print("3. Dán lệnh sau và Enter: [bold white on black] copy(localStorage.getItem('token') || localStorage.getItem('TokenCode') || sessionStorage.getItem('token')) [/bold white on black]")
        console.print("4. Token đã tự động sao chép vào Clipboard. Dán token vào bên dưới:")
        token = click.prompt("Nhập TokenCode/Token")

    ManualAuthenticator.set_ictsv_token(token)
    console.print("[bold green]✓ Đã lưu Token CTSV thành công vào session cache![/bold green]")

@cli.command(name="schedule")
@click.option("--semester", "-s", default=None, help="Mã học kỳ (mặc định: học kỳ active hiện tại)")
def schedule_cmd(semester: Optional[str]):
    """Xem toàn bộ thời khóa biểu học kỳ hiện tại hoặc học kỳ chỉ định."""
    from .crawlers.ehust_crawler import EhustCrawler
    crawler = EhustCrawler()
    
    console.print("[bold cyan]Đang tải thời khóa biểu...[/bold cyan]")
    res = asyncio.run(crawler.get_full_semester_schedule(semester=semester))
        
    if not res.classes:
        console.print("[bold yellow]⚠ Chưa tải được thời khóa biểu (Token eHUST/Portal đã hết hạn hoặc chưa đồng bộ).[/bold yellow]")
        console.print("[bold cyan]👉 Để cập nhật Token trong 5 giây:[/bold cyan]")
        console.print("1. Mở [bold yellow]https://e.hust.edu.vn[/bold yellow] trên Chrome đã đăng nhập.")
        console.print("2. Bấm [bold green]F12[/bold green] -> Tab [bold green]Console[/bold green] -> Dán: [bold white on black] copy(document.cookie) [/bold white on black]")
        console.print("3. Chạy lệnh: [bold green]uv run hust-mcp login-ehust[/bold green] và dán vào.")
        return

    table = Table(title=f"THỜI KHÓA BIỂU HỌC KỲ {res.semester} ({res.total_courses} môn)", show_header=True, header_style="bold magenta")

    table.add_column("STT", justify="center", style="cyan")
    table.add_column("Mã Lớp", style="yellow")
    table.add_column("Mã HP", style="green")
    table.add_column("Tên học phần", style="bold white")
    table.add_column("Hình thức", style="blue")
    table.add_column("Lịch học & Phòng", style="white")
    table.add_column("Vắng", justify="center", style="red")

    for idx, c in enumerate(res.classes, 1):
        table.add_row(
            str(idx),
            str(c.class_id),
            str(c.course_id),
            str(c.course_name),
            str(c.teaching_type),
            str(c.time_range),
            str(c.absence_count)
        )

    console.print(table)




@cli.command(name="clear")
@click.argument("service", type=click.Choice(["ictsv", "ehust", "ctms", "all"]), default="all")
def clear_cmd(service: str):
    """Clear cached sessions and tokens."""
    if service == "all":
        session_manager.clear_all()
        console.print("[bold yellow]Da xoa toan bo session cache.[/bold yellow]")
    else:
        session_manager.clear_service_session(service)
        console.print(f"[bold yellow]Da xoa session cua dich vu {service}.[/bold yellow]")


def main():
    cli()


if __name__ == "__main__":
    main()
