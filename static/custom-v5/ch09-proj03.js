document.addEventListener("DOMContentLoaded", function () {
  const userContentObject = JSON.parse(userContent);
  const stockDataObject = JSON.parse(stockContent);
  //console.log(stockDataObject);
  const stockDetails = document.querySelector(".StockDetails");
  const detailsSection = document.querySelector(".Details");
  const userList = document.querySelector(".UserList ul");
  const stockList = document.querySelector(".StockList");

  // Function to add user data to the list
  function addUser(obj, userList) {
    const li = document.createElement("li");
    li.textContent = `${obj.user.lastname}, ${obj.user.firstname}`;
    li.setAttribute("data-id", obj.id);

    li.addEventListener("click", function () {
      addToUserForm(obj);
      detailsSection.style.display = "block";
    });

    userList.appendChild(li);
  }

  // Function to add user data to the list
  function addToUserList(userListData) {
    userList.innerHTML = "";
    userListData.forEach((user) => {
      addUser(user, userList);
    });
  }

  // Function to add user data to the form
  function addToUserForm(obj) {
    stockDetails.innerHTML = "<h2>Details</h2>";
    const userIdInput = document.getElementById("userID");
    const firstnameInput = document.getElementById("firstname");
    const lastnameInput = document.getElementById("lastname");
    const addressInput = document.getElementById("address");
    const cityInput = document.getElementById("city");
    const emailInput = document.getElementById("email");

    userIdInput.value = obj.id;
    firstnameInput.value = obj.user.firstname;
    lastnameInput.value = obj.user.lastname;
    addressInput.value = obj.user.address;
    cityInput.value = obj.user.city;
    emailInput.value = obj.user.email;

    addPortfolioItems(obj.portfolio);
  }

  // Function to add portfolio items for a user
  function addPortfolioItems(portfolio) {
    stockList.innerHTML = "<h2>Portfolio</h2>";
    portfolio.forEach((item) => {
      const symbol = item.symbol;
      const shares = item.owned;

      const listPortfolio = document.createElement("div");
      listPortfolio.id = "listPortfolio";

      const symbolElement = document.createElement("h3");
      symbolElement.textContent = symbol;
      listPortfolio.appendChild(symbolElement);

      const sharesElement = document.createElement("h3");
      sharesElement.textContent = shares;
      listPortfolio.appendChild(sharesElement);

      const viewButton = document.createElement("button");
      viewButton.textContent = "View";
      viewButton.className = "Button";

      viewButton.addEventListener("click", function () {
        // send the stock symbol here
        showPortfolioItem(item.symbol);
      });

      listPortfolio.appendChild(viewButton);

      stockList.appendChild(listPortfolio); // Append the new listPortfolio div to the StockList
      //console.log(stockList);
    });
  }

  // fucntion to find symbol from stockDataObject
  function findSymbolData(symbol, data) {
    for (let i = 0; i < data.length; i++) {
      if (data[i].symbol === symbol) {
        return data[i];
      }
    }
    return null;
  }

  // Function to display the portfolio stock item details
  function showPortfolioItem(symbol) {
    const data = findSymbolData(symbol, stockDataObject);
    stockDetails.innerHTML = "<h2>Details</h2>";

    const singleStockDiv = document.createElement("div");
    singleStockDiv.id = "singleStock";

    const logoContainerDiv = document.createElement("div");
    logoContainerDiv.className = "logoContainer";

    const logoImg = document.createElement("img");
    logoImg.id = "logo";
    logoImg.src = `https://naveedkhan98.pythonanywhere.com/static/custom-v5/logos/${data.symbol}.svg`;

    const nameLabel = document.createElement("p");
    nameLabel.className = "stockLabel";
    nameLabel.textContent = "Name";

    const stockName = document.createElement("p");
    stockName.id = "stockName";
    stockName.textContent = data.name;

    const sectorLabel = document.createElement("p");
    sectorLabel.className = "stockLabel";
    sectorLabel.textContent = "Sector";

    const stockSector = document.createElement("p");
    stockSector.id = "stockSector";
    stockSector.textContent = data.sector;

    const industryLabel = document.createElement("p");
    industryLabel.className = "stockLabel";
    industryLabel.textContent = "Industry";

    const stockIndustry = document.createElement("p");
    stockIndustry.id = "stockIndustry";
    stockIndustry.textContent = data.subIndustry;

    const addressLabel = document.createElement("p");
    addressLabel.className = "stockLabel";
    addressLabel.textContent = "Address";

    const stockAddress = document.createElement("p");
    stockAddress.id = "stockAddress";
    stockAddress.textContent = data.address;

    singleStockDiv.appendChild(logoContainerDiv);
    logoContainerDiv.appendChild(logoImg);

    singleStockDiv.appendChild(nameLabel);
    singleStockDiv.appendChild(stockName);

    singleStockDiv.appendChild(sectorLabel);
    singleStockDiv.appendChild(stockSector);

    singleStockDiv.appendChild(industryLabel);
    singleStockDiv.appendChild(stockIndustry);

    singleStockDiv.appendChild(addressLabel);
    singleStockDiv.appendChild(stockAddress);

    stockDetails.appendChild(singleStockDiv);
  }

  const saveButton = document.getElementById("btnSave");
  saveButton.addEventListener("click", function (event) {
    event.preventDefault();
    const selectedUserId = document.getElementById("userID").value;
    const updatedUser = userContentObject.find(
      (user) => user.id === parseInt(selectedUserId)
    );

    if (updatedUser) {
      updatedUser.user.firstname = document.getElementById("firstname").value;
      updatedUser.user.lastname = document.getElementById("lastname").value;
      updatedUser.user.address = document.getElementById("address").value;
      updatedUser.user.city = document.getElementById("city").value;
      updatedUser.user.email = document.getElementById("email").value;

      // Update the user list with the modified data
      addToUserList(userContentObject);
    }
  });
  const deleteButton = document.getElementById("btnDelete");
  deleteButton.addEventListener("click", function (event) {
    event.preventDefault();
    const selectedUserId = document.getElementById("userID").value;
    const userIndex = userContentObject.findIndex(
      (user) => user.id === parseInt(selectedUserId)
    );

    if (userIndex !== -1) {
      userContentObject.splice(userIndex, 1);

      // Remove the selected user from the User List
      const userToRemove = userList.querySelector(
        `[data-id="${selectedUserId}"]`
      );
      if (userToRemove) {
        userList.removeChild(userToRemove);
      }

      document.querySelector(".userEntry").reset();
      detailsSection.style.display = "none";
    }
  });

  // set details to none at first to hide it
  detailsSection.style.display = "none";
  addToUserList(userContentObject);
});
