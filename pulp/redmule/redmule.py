import gvsoc
import gvsoc.systree as st

class RedMule(st.Component):

    def __init__(self, parent, name):

        super(RedMule, self).__init__(parent, name)

        self.set_component('pulp.redmule.redmule')

    def i_INPUT(self):
        return self.systree.SlaveItf(self, 'input', signature='io')
    
    def o_OUTPUT(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('output', itf, signature='io')

    def o_IRQ(self):
        return self.systree.MasterItf(self, 'irq', signature='irq') # TODO: check signature (is irq ok?)
