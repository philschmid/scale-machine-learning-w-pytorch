import tarfile
MODEL_NAME = 'cardamage'
with tarfile.open(MODEL_NAME + '.tar.gz', 'w:gz') as f:
    f.add(MODEL_NAME + '.pth')
    f.add('classes.txt')
