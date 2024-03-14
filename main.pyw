from model.model import model
from controller.main import MainController

def main():
    mc = MainController('main')
    mc.view.mainloop()
    mc.close()
    model.close()

if __name__ == '__main__':
    main()
    
    
