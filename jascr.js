function setChBoxStateAsThis(chBox, cbClassName) {
  let cbList = document.getElementsByClassName(cbClassName)
  let len = cbList.length
  for (let i = 0; i < len; i++) {
    if (cbList.item(i).type && cbList.item(i).type == "checkbox") {
      cbList.item(i).checked = chBox.checked
    }
  }
}
function setSameNamedChBoxState(chBox) {
  let cbList = document.getElementsByName(chBox.name)
  let len = cbList.length
  for (let i = 0; i < len; i++) {
    if (cbList.item(i).type && cbList.item(i).type == "checkbox") {
      cbList.item(i).checked = chBox.checked
    }
  }
}
function setEnableChBox(chBox, elemId) {
  let elem = document.getElementById(elemId)
  // if (elem.hasAttribute("contenteditable")) {
      // elem.contenteditable = chBox.checked  
  // }
  elem.disabled = !(chBox.checked)
}
function setHiddenField(hfId, hfVal) {
  let hf = document.getElementById(hfId)
  if (hf.hasAttribute("value")) {
    hf.value = hfVal
  }
}

function actChanged(obj, class_name) {
  let cellList = document.getElementsByClassName(class_name);
  let len = cellList.length;
  let col_content = document.getElementById('col_content_' + class_name);
  if (obj.value == 'from_field') {
    col_content.removeAttribute('readonly');
    col_content.style.backgroundColor = '#AFA';
    col_content.style.color = '#060';
  } else {
    col_content.setAttribute('readonly','true');
    col_content.style.backgroundColor = '';
    col_content.style.color = '';
  }
  for (let i = 0; i < len; i++) {
    cellList.item(i).disabled = !(obj.value == 'edit');
    if (obj.value == 'delete') {
      // cellList.item(i).classList.remove('active_green');
      // cellList.item(i).classList.add('active_red');
      cellList.item(i).setAttribute('readonly','true');
      cellList.item(i).style.backgroundColor = '#FAA';
      cellList.item(i).style.color = '#800';
    } else if (obj.value == 'edit') {
      // cellList.item(i).classList.remove('active_red');
      // cellList.item(i).classList.add('active_green');
      cellList.item(i).removeAttribute('readonly');
      cellList.item(i).style.backgroundColor = '#AFA';
      cellList.item(i).style.color = '#080';
    } else {
      // cellList.item(i).classList.remove('active_green');
      // cellList.item(i).classList.remove('active_red');
      cellList.item(i).setAttribute('readonly','true');
      cellList.item(i).style.backgroundColor = '';
      cellList.item(i).style.color = '';
    }
  }
  //here class_name is a col_name, so col_content textarea id is like here:
}

function setUseFilterCell(chBox, cellId) {
  let el = document.getElementById(cellId)
  el.classList.toggle('active_green');
}

//to change number input maximum when some value is selected:
function setNumFieldMax(numFieldId, selectedVal, valToMax) {
  const valMap = new Map(valToMax)
  let nf = document.getElementById(numFieldId);
  nf.setAttribute('max', valMap.get(selectedVal));
}

function showElem(elemId) {
  let el = document.getElementById(elemId);
  el.scrollIntoView({inline:"end"});
}















