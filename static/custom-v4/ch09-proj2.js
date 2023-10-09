document.addEventListener("DOMContentLoaded", function () {
  const photos = JSON.parse(content);
  console.log(photos);

  const imageList = document.getElementById("paintings");
  const titleElement = document.getElementById("title");
  const artistElement = document.getElementById("artist");
  const fullImageElement = document.getElementById("full");
  const descriptionElement = document.getElementById("description");
  const figureSections = document.getElementById("image-sections");

  function removeChildDivs() {
    const divElements = figureSections.querySelectorAll("div.box");
    divElements.forEach(function (divElement) {
      figureSections.removeChild(divElement);
    });
  }

  function handleImageClick(item) {
    console.log(figureSections.children);
    titleElement.textContent = item.title;
    artistElement.textContent = item.artist;
    fullImageElement.src = "https://naveedkhan98.pythonanywhere.com/static/custom-v4/images/large/" + item.id + ".jpg";
    for (const feature of item.features) {
      const boxDiv = document.createElement("div");
      boxDiv.className = "box";
      const left = feature.upperLeft[0];
      const top = feature.upperLeft[1];
      const width = feature.lowerRight[0] - feature.upperLeft[0];
      const height = feature.lowerRight[1] - feature.upperLeft[1];

      boxDiv.style.position = "absolute";
      boxDiv.style.left = left + "px";
      boxDiv.style.top = top + "px";
      boxDiv.style.width = width + "px";
      boxDiv.style.height = height + "px";

      boxDiv.addEventListener("mouseover", function () {
        descriptionElement.textContent = feature.description;
      });
      console.log(figureSections);
      figureSections.append(boxDiv);
    }
  }

  for (const item of photos) {
    const listItem = document.createElement("ul");
    const imgElement = document.createElement("img");
    imgElement.className = "full";
    imgElement.src = "https://naveedkhan98.pythonanywhere.com/static/custom-v4/images/small/" + item.id + ".jpg";
    listItem.dataset.id = item.id;
    imgElement.addEventListener("click", function () {
      removeChildDivs();
      handleImageClick(item);
    });

    listItem.appendChild(imgElement);
    imageList.appendChild(listItem);
  }
});
