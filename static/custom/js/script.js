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

  fetch("https://naveedkhan98.pythonanywhere.com/api/message/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  })
    .then(function (response) {
      if (response.status === 201) {
        // Successful response
        alert("Message sent successfully!");
      } else {
        // Error response
        alert("Error sending message. Please try again later.");
      }
    })
    .catch(function (error) {
      // Network error or other issues
      alert("An error occurred while sending the message. Please try again later.");
    });
}
