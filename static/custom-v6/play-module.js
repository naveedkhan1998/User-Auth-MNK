export class Speech {
  constructor(speaker, lines) {
    this.speaker = speaker;
    this.lines = lines;
  }

  render() {
    const speechElement = document.createElement("div");
    speechElement.classList.add("speech");

    const speakerSpan = document.createElement("span");
    speakerSpan.textContent = this.speaker;
    speechElement.appendChild(speakerSpan);

    this.lines.forEach((line) => {
      const lineParagraph = document.createElement("p");
      lineParagraph.innerHTML = line; // Use innerHTML to interpret HTML tags
      speechElement.appendChild(lineParagraph);
    });

    return speechElement;
  }
}

export class Scene {
  constructor(name, title, stageDirection) {
    this.name = name;
    this.title = title;
    this.stageDirection = stageDirection;
    this.speeches = [];
  }

  addSpeech(speech) {
    this.speeches.push(speech);
  }

  getSpeakers() {
    const speakers = new Set();
    this.speeches.forEach((speech) => {
      speakers.add(speech.speaker);
    });
    return Array.from(speakers);
  }

  filterSpeechesByPlayer(player) {
    this.speeches = this.speeches.filter((speech) => speech.speaker === player);
  }
  highlightSpeeches(regex) {
    this.speeches.forEach((speech) => {
      speech.lines = speech.lines.map((line) => {
        const matches = line.match(regex);
        if (matches) {
          matches.forEach((match) => {
            line = line.replace(match, `<b>${match}</b>`);
          });
        }
        return line;
      });
    });
  }

  render() {
    const sceneElement = document.createElement("div");
    sceneElement.classList.add("scene");

    const sceneName = document.createElement("h4");
    sceneName.textContent = this.name;
    sceneElement.appendChild(sceneName);

    const sceneTitle = document.createElement("p");
    sceneTitle.classList.add("title");
    sceneTitle.textContent = this.title;
    sceneElement.appendChild(sceneTitle);

    const stageDirection = document.createElement("p");
    stageDirection.classList.add("direction");
    stageDirection.textContent = this.stageDirection;
    sceneElement.appendChild(stageDirection);

    this.speeches.forEach((speech) => {
      const speechElement = speech.render();
      sceneElement.appendChild(speechElement);
    });

    return sceneElement;
  }
}

export class Act {
  constructor(name) {
    this.name = name;
    this.scenes = [];
  }

  addScene(scene) {
    this.scenes.push(scene);
  }

  render() {
    const actElement = document.createElement("div");

    const nameHeader = document.createElement("h3");
    nameHeader.textContent = this.name;
    actElement.appendChild(nameHeader);

    this.scenes.forEach((scene) => {
      const sceneElement = scene.render();
      actElement.appendChild(sceneElement);
    });

    return actElement;
  }
}

export class Play {
  constructor(title, short, personas, acts) {
    this.title = title;
    this.short = short;
    this.personas = personas;
    this.acts = acts;
    this.selectedAct = null;
    this.selectedScene = null;
  }

  addAct(act) {
    this.acts.push(act);
  }

  selectAct(actName) {
    this.selectedAct = this.acts.find((act) => act.name === actName);
  }

  selectScene(sceneName) {
    for (const act of this.acts) {
      for (const scene of act.scenes) {
        if (scene.name === sceneName) {
          this.selectedScene = scene;
          return;
        }
      }
    }
  }

  render() {
    const playElement = document.createElement("div");
    playElement.classList.add("play");

    const titleHeader = document.createElement("h2");
    titleHeader.textContent = this.title;
    playElement.appendChild(titleHeader);

    if (this.selectedAct && this.selectedScene) {
      const actElement = document.createElement("h3");
      actElement.textContent = this.selectedAct.name;
      playElement.appendChild(actElement);

      const sceneElement = this.selectedScene.render();
      playElement.appendChild(sceneElement);
    }

    return playElement;
  }
}
