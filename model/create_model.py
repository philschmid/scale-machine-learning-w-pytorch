import tarfile

MODEL_NAME = 'cardamage'


def create_model_zip(model_name='', out_dir='./', model=None, class_list=[]):
    if model != None:
        print('Saving model as .pth')
        import torch
        torch.save(model, out_dir + model_name+'.pth')
    if len(class_list > 1):
        print('Creating classes.txt')
        with open(out_dir + 'classes.txt', 'w') as filehandle:
            for listitem in class_list:
                filehandle.write('%s\n' % listitem)
    print('zipping model as tar.gz')
    with tarfile.open(out_dir + model_name + '.tar.gz', 'w:gz') as f:
        f.add(model_name+'.pth')
        f.add('classes.txt')


if __name__ == "__main__":
    classes = ['00-damage', '01-whole']
    create_model_zip(model_name=MODEL_NAME, class_list=classes)
