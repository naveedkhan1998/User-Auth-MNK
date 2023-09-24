const benefits = document.querySelectorAll(".benefit");

function checkInView() {
  benefits.forEach((benefit) => {
    const benefitTop = benefit.getBoundingClientRect().top;
    const windowHeight = window.innerHeight;
    if (benefitTop < windowHeight * 1) {
      benefit.classList.add("show");
    } else {
      benefit.classList.remove("show");
    }
  });
}

window.addEventListener("scroll", checkInView);
window.addEventListener("resize", checkInView);
checkInView();

const scrollToTopButton = document.getElementById("scrollToTopBtn");
function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}
window.addEventListener("scroll", () => {
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    scrollToTopButton.style.display = "block";
  } else {
    scrollToTopButton.style.display = "none";
  }
});
scrollToTopButton.addEventListener("click", scrollToTop);

function showPopup(event) {
  event.preventDefault();
  var name = document.getElementById("name").value;
  var email = document.getElementById("email").value;
  var message = document.getElementById("message").value;

  var formData = {
    name: name,
    email: email,
    message: message,
  };

  var jsonData = JSON.stringify(formData);

  var xhr = new XMLHttpRequest();

  xhr.open(
    "POST",
    "https://naveedkhan98.pythonanywhere.com/api/message/",
    true
  );
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
      alert("Message sent successfully!");
    } else if (xhr.readyState === 4 && xhr.status !== 200) {
      alert("Error sending message. Please try again later.");
    }
  };

  xhr.send(jsonData);
}
