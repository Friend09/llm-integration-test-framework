"""Tests for .NET scanner functionality."""

import pytest
from pathlib import Path

from src.scanner.dotnet_scanner import DotNetScanner
from src.utils.file_utils import safe_write_file, ensure_directory


@pytest.fixture
def dotnet_test_repo(tmp_path):
    """Create a test repository with C# files."""
    files = {
        "Controllers/UserController.cs": """
using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using MyApp.Models;
using MyApp.Services;

namespace MyApp.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class UserController : ControllerBase
    {
        private readonly IUserService _userService;

        public UserController(IUserService userService)
        {
            _userService = userService;
        }

        [HttpGet("{id}")]
        public async Task<ActionResult<User>> GetUser(int id)
        {
            var user = await _userService.GetUserAsync(id);
            if (user == null)
                return NotFound();
            return user;
        }

        [HttpPost]
        public async Task<ActionResult<User>> CreateUser([FromBody] User user)
        {
            var created = await _userService.CreateUserAsync(user);
            return CreatedAtAction(nameof(GetUser), new { id = created.Id }, created);
        }
    }
}""",
        "Models/User.cs": """
using System;
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        public int Id { get; set; }

        [Required]
        public string Name { get; set; }

        [Required]
        [EmailAddress]
        public string Email { get; set; }

        public DateTime CreatedAt { get; set; }
    }
}""",
        "Services/IUserService.cs": """
using System.Threading.Tasks;
using MyApp.Models;

namespace MyApp.Services
{
    public interface IUserService
    {
        Task<User> GetUserAsync(int id);
        Task<User> CreateUserAsync(User user);
    }
}""",
        "Services/UserService.cs": """
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Models;

namespace MyApp.Services
{
    public class UserService : IUserService
    {
        private readonly AppDbContext _context;

        public UserService(AppDbContext context)
        {
            _context = context;
        }

        public async Task<User> GetUserAsync(int id)
        {
            return await _context.Users.FindAsync(id);
        }

        public async Task<User> CreateUserAsync(User user)
        {
            _context.Users.Add(user);
            await _context.SaveChangesAsync();
            return user;
        }
    }
}"""
    }

    for path, content in files.items():
        full_path = tmp_path / path
        ensure_directory(full_path.parent)
        safe_write_file(full_path, content)

    return tmp_path


def test_namespace_detection(dotnet_test_repo):
    """Test namespace detection in C# files."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check that all namespaces are detected
    namespaces = {comp.name for comp in graph.get_components() if comp.component_type == "namespace"}
    assert "MyApp.Controllers" in namespaces
    assert "MyApp.Models" in namespaces
    assert "MyApp.Services" in namespaces


def test_class_detection(dotnet_test_repo):
    """Test class detection and inheritance."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check that classes are detected with correct inheritance
    user_controller = graph.get_component("MyApp.Controllers.UserController")
    assert user_controller is not None
    assert user_controller.component_type == "class"

    # Check inheritance dependencies
    controller_deps = graph.get_dependencies("MyApp.Controllers.UserController")
    assert any(
        dep.target_component == "ControllerBase" and dep.dependency_type == "inherits"
        for dep in controller_deps
    )


def test_method_detection(dotnet_test_repo):
    """Test method detection and endpoint identification."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check that API methods are detected as endpoints
    get_user = graph.get_component("MyApp.Controllers.UserController.GetUser")
    assert get_user is not None
    assert get_user.is_integration_point

    create_user = graph.get_component("MyApp.Controllers.UserController.CreateUser")
    assert create_user is not None
    assert create_user.is_integration_point


def test_using_dependencies(dotnet_test_repo):
    """Test using directive dependency tracking."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check using dependencies in UserController
    controller_deps = graph.get_dependencies("MyApp.Controllers")
    assert any(
        dep.target_component == "Microsoft.AspNetCore.Mvc" and dep.dependency_type == "using"
        for dep in controller_deps
    )
    assert any(
        dep.target_component == "MyApp.Models" and dep.dependency_type == "using"
        for dep in controller_deps
    )


def test_property_detection(dotnet_test_repo):
    """Test property detection in model classes."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check User model properties
    user_class = graph.get_component("MyApp.Models.User")
    assert user_class is not None

    # Properties should be added as components
    id_prop = graph.get_component("MyApp.Models.User.Id")
    assert id_prop is not None
    name_prop = graph.get_component("MyApp.Models.User.Name")
    assert name_prop is not None
    email_prop = graph.get_component("MyApp.Models.User.Email")
    assert email_prop is not None


def test_integration_point_detection(dotnet_test_repo):
    """Test detection of various integration points."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Controller should be identified as an integration point
    user_controller = graph.get_component("MyApp.Controllers.UserController")
    assert user_controller.is_integration_point

    # Service methods should not be integration points
    user_service = graph.get_component("MyApp.Services.UserService")
    assert not user_service.is_integration_point


def test_attribute_detection(dotnet_test_repo):
    """Test detection and handling of C# attributes."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check required attribute on User properties
    email_prop = graph.get_component("MyApp.Models.User.Email")
    assert email_prop is not None
    # Note: In a more complete implementation, we would store and check attributes
    # on the components themselves


def test_dependency_graph_structure(dotnet_test_repo):
    """Test overall structure of the dependency graph."""
    scanner = DotNetScanner(dotnet_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check namespace hierarchy
    assert graph.get_component("MyApp.Controllers") is not None
    assert graph.get_component("MyApp.Models") is not None
    assert graph.get_component("MyApp.Services") is not None

    # Check class dependencies
    controller_deps = graph.get_dependencies("MyApp.Controllers.UserController")
    assert any(
        dep.target_component == "MyApp.Services.IUserService"
        for dep in controller_deps
    )

    # Check interface implementation
    service_deps = graph.get_dependencies("MyApp.Services.UserService")
    assert any(
        dep.target_component == "MyApp.Services.IUserService" and dep.dependency_type == "implements"
        for dep in service_deps
    )

# Point to a .NET project directory
scanner = DotNetScanner(Path("path/to/dotnet/project"))
scanner.scan()

# Get dependency graph
graph = scanner.dependency_graph

# View components and relationships
components = graph.get_components()
dependencies = graph.get_dependencies()
