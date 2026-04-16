// ML Models Loader
let foodModel = null;
let bodyModel = null;

async function loadModels() {
    try {
        const modelURL = 'https://tfhub.dev/google/tfjs-model/imagenet/mobilenet_v2_100_224/feature_vector/5/default/1';
        foodModel = await tf.loadGraphModel(modelURL, { fromTFHub: true });
        console.log('Food model loaded');
    } catch (e) {
        console.log('Using fallback detection');
    }
}

loadModels();
