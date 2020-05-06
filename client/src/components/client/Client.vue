<template>
  <div style="height: calc(100vh - 112px)">
    <Splitpanes>
      <Pane size="20" min-size="10">
        <span>1</span>
      </Pane>
      <Pane size="80" min-size="10">
        <Splitpanes horizontal>
          <Pane size="90">
            <span>2</span>
          </Pane>
          <Pane size="10" min-size="10">
            <span>3</span>
          </Pane>
        </Splitpanes>
      </Pane>
    </Splitpanes>
  </div>
</template>

<style>
.splitpanes__pane {
  box-shadow: 0 0 3px rgba(0, 0, 0, .2) inset;
  justify-content: center;
  align-items: center;
  display: flex;
  position: relative;
}
.container {
  padding: 0px;
}
.splitpanes--vertical > .splitpanes__splitter {
  min-width: 3px;
}
.splitpanes--horizontal > .splitpanes__splitter {
  min-height: 3px;
}

</style>

<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

export default {
  data() {
    return {
      
      
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: { Splitpanes, Pane },
  created() {
  },
  methods: {
  }
}
</script>