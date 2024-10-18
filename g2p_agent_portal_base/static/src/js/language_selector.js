// Select the language dropdown button
const dropdownButton = document.querySelector(".language-dropdown button");

// Add an event listener to the dropdown button that will toggle the dropdown menu
dropdownButton.addEventListener("click", function () {
    this.classList.toggle("active");
});

// Add an event listener to the document that will close the dropdown menu if the user clicks outside the menu
document.addEventListener("click", function (event) {
    if (
        !event.target.matches(".language-dropdown button") &&
        !event.target.matches(".language-dropdown .dropdown-menu *")
    ) {
        dropdownButton.classList.remove("active");
    }
});

// Add an event listener to the dropdown menu items that will update the text of the button with the selected language
const dropdownItems = document.querySelectorAll(".dropdown-item");
dropdownItems.forEach(function (item) {
    item.addEventListener("click", function () {
        const languageText = this.querySelector("span").textContent;
        console.log(languageText);
        const languageFlag = this.querySelector("img").src;
        const button = document.querySelector(".language-dropdown button");
        const buttonSpan = button.querySelector("span");
        const buttonFlag = button.querySelector("img");
        buttonSpan.textContent = languageText;
        buttonFlag.src = languageFlag;
        buttonFlag.alt = languageText;
        localStorage.setItem("selectedLanguage", languageText);
    });
});

// Check if a language has already been selected and update the button text and image accordingly
if (localStorage.getItem("selectedLanguage")) {
    const selectedLanguage = localStorage.getItem("selectedLanguage");

    dropdownItems.forEach(function (item) {
        const languageText = item.querySelector("span");
        if (languageText && languageText.textContent === selectedLanguage) {
            const languageFlag = item.querySelector("img").src;
            const button = document.querySelector(".language-dropdown button");
            const buttonSpan = button.querySelector("span");
            const buttonFlag = button.querySelector("img");
            buttonSpan.textContent = selectedLanguage;
            buttonFlag.src = languageFlag;
            buttonFlag.alt = selectedLanguage;
        }
    });
}
