/*
To get a specific play, add play name via query string, 
e.g., url = url + '?name=hamlet';

https://www.randyconnolly.com/funwebdev/3rd/api/shakespeare/play.php?name=hamlet
https://www.randyconnolly.com/funwebdev/3rd/api/shakespeare/play.php?name=jcaesar

*/

/* note: you may get a CORS error if you test this locally (i.e., directly from a
  local file). To work correctly, this needs to be tested on a local web server.  
  Some possibilities: if using Visual Code, use Live Server extension; if Brackets,
  use built-in Live Preview.
  */

// Define the API endpoint URL

import { Play, Act, Scene, Speech } from "./play-module.js";

const apiUrl =
  "https://www.randyconnolly.com/funwebdev/3rd/api/shakespeare/play.php";

document.addEventListener("DOMContentLoaded", function () {
  const interface_ = document.getElementById("interface");
  const playListSelect = document.getElementById("playList");
  const actListSelect = document.getElementById("actList");
  const sceneListSelect = document.getElementById("sceneList");
  const playerListSelect = document.getElementById("playerList");
  const playHere = document.getElementById("playHere");
  const txtHighlight = document.getElementById("txtHighlight");
  const btnHighlight = document.getElementById("btnHighlight");

  let selectedPlay = null;
  let selectedActName = null;
  let selectedSceneName = null;
  interface_.style.display = "none";

  function createPlay(playData) {
    const { title, short, persona, acts } = playData;
    const play = new Play(title, short, persona, []);

    acts.forEach((actData) => {
      const act = new Act(actData.name);
      actData.scenes.forEach((sceneData) => {
        const scene = new Scene(
          sceneData.name,
          sceneData.title,
          sceneData.stageDirection
        );
        sceneData.speeches.forEach((speechData) => {
          const speech = new Speech(speechData.speaker, speechData.lines);
          scene.addSpeech(speech);
        });
        act.addScene(scene);
      });
      play.addAct(act);
    });

    return play;
  }

  function renderPlay() {
    playHere.innerHTML = "";
    playHere.appendChild(selectedPlay.render());
  }

  function populateSelectList(selectElement, options) {
    selectElement.innerHTML = "";
    options.forEach((option) => {
      const optionElement = document.createElement("option");
      optionElement.value = option;
      optionElement.textContent = option;
      selectElement.appendChild(optionElement);
    });
  }

  function populateActList() {
    const actNames = selectedPlay.acts.map((act) => act.name);
    populateSelectList(actListSelect, actNames);
    if (actNames.length > 0) {
      selectedActName = actNames[0];
      actListSelect.value = selectedActName;
      selectAct(selectedActName);
    }
  }

  function populateSceneList(selectedActName) {
    const scenesInSelectedAct = selectedPlay.acts.find(
      (act) => act.name === selectedActName
    ).scenes;
    const sceneNames = scenesInSelectedAct.map((scene) => scene.name);
    populateSelectList(sceneListSelect, sceneNames);
    if (sceneNames.length > 0) {
      selectedSceneName = sceneNames[0];
      sceneListSelect.value = selectedSceneName;
      selectScene(selectedSceneName);
    }
  }

  function populatePlayerList(selectedSceneName) {
    const scene = selectedPlay.selectedAct.scenes.find(
      (s) => s.name === selectedSceneName
    );
    const speakers = scene.getSpeakers();
    populateSelectList(playerListSelect, speakers);
  }

  function selectAct(selectedActName) {
    const selectedAct = selectedPlay.acts.find(
      (act) => act.name === selectedActName
    );
    if (selectedAct) {
      selectedPlay.selectedAct = selectedAct;
    }
  }

  function selectScene(selectedSceneName) {
    if (selectedPlay.selectedAct) {
      const selectedScene = selectedPlay.selectedAct.scenes.find(
        (scene) => scene.name === selectedSceneName
      );
      if (selectedScene) {
        selectedPlay.selectedScene = selectedScene;
        populatePlayerList(selectedSceneName);
      }
    }
  }

  function fetchPlayData(selectedPlayName) {
    fetch(`${apiUrl}?name=${selectedPlayName}`)
      .then((response) => response.json())
      .then((data) => {
        selectedPlay = createPlay(data);

        selectedActName = data.acts[0].name;
        selectedSceneName = data.acts[0].scenes[0].name;

        populateActList();
        populateSceneList(selectedActName);
        selectAct(selectedActName);
        selectScene(selectedSceneName);
        populatePlayerList(selectedSceneName);

        renderPlay();
        interface_.style.display = "block";
      })
      .catch((error) => console.error("Error:", error));
  }

  playListSelect.addEventListener("change", function () {
    const selectedPlayName = playListSelect.value;
    fetchPlayData(selectedPlayName);
  });

  actListSelect.addEventListener("change", function () {
    const selectedActName = actListSelect.value;
    selectAct(selectedActName);
    populateSceneList(selectedActName);
    renderPlay();
  });

  sceneListSelect.addEventListener("change", function () {
    const selectedSceneName = sceneListSelect.value;
    selectScene(selectedSceneName);
    populatePlayerList(selectedSceneName);
    renderPlay();
  });

  btnHighlight.addEventListener("click", function () {
    const selectedPlayer = playerListSelect.value;
    const searchTerm = txtHighlight.value;

    if (selectedPlay && selectedPlayer !== "0") {
      selectedPlay.selectedScene.filterSpeechesByPlayer(selectedPlayer);

      if (searchTerm) {
        const regex = new RegExp(searchTerm, "gi");
        selectedPlay.selectedScene.highlightSpeeches(regex);
      }

      renderPlay();
    }
  });
});
