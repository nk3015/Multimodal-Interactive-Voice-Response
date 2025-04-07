const toggleSwitch = document.getElementById("darkModeToggle");

// Function to apply theme
function applyTheme(theme) {
  document.body.classList.remove("dark-mode", "light-mode");
  if (theme === "dark") {
    document.body.classList.add("dark-mode");
    toggleSwitch.checked = true;
  } else {
    document.body.classList.add("light-mode");
    toggleSwitch.checked = false;
  }
}

// Check for saved preference in localStorage
let savedTheme = localStorage.getItem("theme");

if (!savedTheme) {
  savedTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

applyTheme(savedTheme);

// Toggle theme and save preference
toggleSwitch.addEventListener("change", () => {
  savedTheme = toggleSwitch.checked ? "dark" : "light";
  localStorage.setItem("theme", savedTheme);
  applyTheme(savedTheme);
});
