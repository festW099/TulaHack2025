const mapBorn = L.map('map-born').setView([55.751244, 37.618423], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mapBorn);

const mapBattles = L.map('map-battles').setView([55.751244, 37.618423], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mapBattles);

let bornMarker = null;
mapBorn.on('click', function(e) {
    if (bornMarker) mapBorn.removeLayer(bornMarker);
    bornMarker = L.marker(e.latlng).addTo(mapBorn).bindPopup("Место рождения").openPopup();
    document.getElementById('born-coords').textContent = `Широта: ${e.latlng.lat.toFixed(6)}, Долгота: ${e.latlng.lng.toFixed(6)}`;
    document.getElementById('born_latitude').value = e.latlng.lat;
    document.getElementById('born_longitude').value = e.latlng.lng;
});

let battleMarkers = [];
let battleLocations = [];

function addBattleMarker() {
    const center = mapBattles.getCenter();
    const marker = L.marker(center, {draggable: true}).addTo(mapBattles).bindPopup("Место битвы").openPopup();
    battleMarkers.push(marker);
    battleLocations.push({lat: center.lat, lng: center.lng});
    updateBattleMarkersList();
    updateBattleLocationsInput();
    marker.on('dragend', function(e) {
        const index = battleMarkers.indexOf(marker);
        if (index !== -1) {
            battleLocations[index] = e.target.getLatLng();
            updateBattleMarkersList();
            updateBattleLocationsInput();
        }
    });
}

function updateBattleMarkersList() {
    const list = document.getElementById('battle-marker-list');
    list.innerHTML = '';
    battleLocations.forEach((loc, index) => {
        const item = document.createElement('div');
        item.innerHTML = `Битва ${index + 1}: Широта: ${loc.lat.toFixed(6)}, Долгота: ${loc.lng.toFixed(6)} <button type="button" onclick="removeBattleMarker(${index})">Удалить</button>`;
        list.appendChild(item);
    });
}

function removeBattleMarker(index) {
    if (index >= 0 && index < battleMarkers.length) {
        mapBattles.removeLayer(battleMarkers[index]);
        battleMarkers.splice(index, 1);
        battleLocations.splice(index, 1);
        updateBattleMarkersList();
        updateBattleLocationsInput();
    }
}

function updateBattleLocationsInput() {
    document.getElementById('battle_locations').value = JSON.stringify(battleLocations);
}

let awards = [];

function addAwardField() {
    const awardsList = document.getElementById('awards-list');
    const awardId = Date.now();
    const awardDiv = document.createElement('div');
    awardDiv.className = 'award-item';
    awardDiv.innerHTML = `
        <input type="text" id="award-${awardId}" placeholder="Название награды">
        <button type="button" onclick="removeAward('${awardId}')">Удалить</button>
    `;
    awardsList.appendChild(awardDiv);
    awards.push({id: awardId, value: ''});
    document.getElementById(`award-${awardId}`).addEventListener('input', function() {
        updateAwardsInput();
    });
}

function removeAward(id) {
    awards = awards.filter(award => award.id !== id);
    document.getElementById(`award-${id}`).parentElement.remove();
    updateAwardsInput();
}

function updateAwardsInput() {
    awards.forEach(award => {
        const input = document.getElementById(`award-${award.id}`);
        if (input) award.value = input.value;
    });
    document.getElementById('awards-input').value = JSON.stringify(awards.map(a => a.value));
}

let photoCount = 0;
const photoUploadContainer = document.getElementById('photo-upload-container');
const photoPreview = document.getElementById('photo-preview');

function addPhotoField() {
    photoCount++;
    const photoId = `photo-${photoCount}`;
    const photoDiv = document.createElement('div');
    photoDiv.className = 'photo-upload-item';
    photoDiv.innerHTML = `
        <input type="file" name="photos" id="${photoId}" accept="image/*" onchange="handlePhotoUpload(this)">
        <button type="button" onclick="removePhotoField('${photoId}')">Удалить</button>
    `;
    photoUploadContainer.appendChild(photoDiv);
}

function handlePhotoUpload(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item-container';
            previewItem.dataset.id = input.id;
            previewItem.innerHTML = `
                <img src="${e.target.result}" class="preview-item">
                <button type="button" onclick="removePreview('${input.id}')">×</button>
            `;
            photoPreview.appendChild(previewItem);
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function removePhotoField(id) {
    const field = document.getElementById(id).parentElement;
    if (field) field.remove();
    removePreview(id);
}

function removePreview(id) {
    const previews = document.querySelectorAll(`.preview-item-container[data-id="${id}"]`);
    previews.forEach(preview => preview.remove());
}

document.getElementById('letter-photo-upload').addEventListener('change', function(e) {
    const preview = document.getElementById('letter-photo-preview');
    preview.innerHTML = '';
    const file = e.target.files[0];
    if (file && file.type.match('image.*')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'preview-item';
            preview.appendChild(img);
        }
        reader.readAsDataURL(file);
    }
});

function prepareFormData() {
    if (!document.getElementById('born_latitude').value || !document.getElementById('born_longitude').value) {
        alert('Пожалуйста, укажите место рождения на карте');
        return false;
    }
    
    const photoInputs = document.querySelectorAll('input[name="photos"]');
    let hasPhotos = false;
    photoInputs.forEach(input => {
        if (input.files.length > 0) hasPhotos = true;
    });
    
    if (!hasPhotos) {
        alert('Пожалуйста, загрузите хотя бы одну фотографию');
        return false;
    }
    
    if (!document.getElementById('letter-photo-upload').files.length) {
        alert('Пожалуйста, загрузите фото письма');
        return false;
    }
    
    updateAwardsInput();
    return true;
}

window.onload = function() {
    addPhotoField();
};

window.removeBattleMarker = removeBattleMarker;
window.removeAward = removeAward;

function addPhotoField() {
    const input = document.getElementById('photo-upload');
    input.click();
    
    input.onchange = function() {
        const files = input.files;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const previewContainer = document.createElement('div');
                previewContainer.className = 'preview-container';
                
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'preview-item';
                
                previewContainer.appendChild(img);
                document.getElementById('photo-preview').appendChild(previewContainer);
            }
            
            reader.readAsDataURL(file);
        }
    };
}