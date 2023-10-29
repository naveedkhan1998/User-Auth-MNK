import { Play, Act, Scene, Speech } from "./play-module.js";

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
const apiUrl =
  "https://www.randyconnolly.com/funwebdev/3rd/api/shakespeare/play.php";

// DOM elements
document.addEventListener("DOMContentLoaded", function () {
  const playListSelect = document.getElementById("playList");
  const actListSelect = document.getElementById("actList");
  const sceneListSelect = document.getElementById("sceneList");
  const playerListSelect = document.getElementById("playerList");
  const playHere = document.getElementById("playHere");
  const txtHighlight = document.getElementById("txtHighlight");
  const btnHighlight = document.getElementById("btnHighlight");

  let selectedPlay = null;
  let selectedActName = null; // Keep track of the selected act
  let selectedSceneName = null; // Keep track of the selected scene

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

  function populateActList() {
    actListSelect.innerHTML = "";

    selectedPlay.acts.forEach((act) => {
      const option = document.createElement("option");
      option.value = act.name;
      option.textContent = act.name;
      actListSelect.appendChild(option);
    });

    // Select the first act automatically
    if (selectedPlay.acts.length > 0) {
      selectedActName = selectedPlay.acts[0].name;
      actListSelect.value = selectedActName;
      selectAct(selectedActName);
    }
  }

  function populateSceneList(selectedActName) {
    sceneListSelect.innerHTML = "";

    const scenesInSelectedAct = selectedPlay.acts.find(
      (act) => act.name === selectedActName
    ).scenes;

    scenesInSelectedAct.forEach((scene) => {
      const option = document.createElement("option");
      option.value = scene.name;
      option.textContent = scene.name;
      sceneListSelect.appendChild(option);
    });

    // Select the first scene automatically
    if (scenesInSelectedAct.length > 0) {
      selectedSceneName = scenesInSelectedAct[0].name;
      sceneListSelect.value = selectedSceneName;
      selectScene(selectedSceneName);
    }
  }

  function populatePlayerList(selectedSceneName) {
    playerListSelect.innerHTML = "";

    const scene = selectedPlay.selectedAct.scenes.find(
      (s) => s.name === selectedSceneName
    );
    const speakers = scene.getSpeakers();

    speakers.forEach((speaker) => {
      const option = document.createElement("option");
      option.value = speaker;
      option.textContent = speaker;
      playerListSelect.appendChild(option);
    });
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
      }
    }
  }

  playListSelect.addEventListener("change", function () {
    const selectedPlayName = playListSelect.value;

    fetch(`${apiUrl}?name=${selectedPlayName}`)
      .then((response) => response.json())
      .then((data) => {
        selectedPlay = createPlay(data);

        // For initial setup
        selectedActName = data.acts[0].name;
        selectedSceneName = data.acts[0].scenes[0].name;

        // Populate the act and scene lists with defaults
        populateActList();
        populateSceneList(selectedActName);

        // Populate the player list based on the default values
        selectAct(selectedActName);
        selectScene(selectedSceneName);
        populatePlayerList(selectedSceneName);

        renderPlay();
      })
      .catch((error) => console.error("Error:", error));
  });
  actListSelect.addEventListener("change", function () {
    let selectedActName = actListSelect.value;
    selectedActName = selectedActName;
    selectAct(selectedActName);
    populateSceneList(selectedActName);
    renderPlay();
  });

  sceneListSelect.addEventListener("change", function () {
    let selectedSceneName = sceneListSelect.value;
    selectScene(selectedSceneName);
    populatePlayerList(selectedSceneName);
    renderPlay();
  });

  btnHighlight.addEventListener("click", function () {
    const selectedPlayer = playerListSelect.value;
    const searchTerm = txtHighlight.value;

    if (selectedPlay && selectedPlayer !== "0") {
      // Filter speeches for the selected player
      selectedPlay.selectedScene.filterSpeechesByPlayer(selectedPlayer);

      // If a search term is entered, highlight the text
      if (searchTerm) {
        const regex = new RegExp(searchTerm, "gi");
        selectedPlay.selectedScene.highlightSpeeches(regex);
      }

      // Re-render the play to reflect the filtered and highlighted speeches
      renderPlay();
    }
  });
});
