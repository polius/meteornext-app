<template>
  <div>
    <!---------->
    <!-- INFO -->
    <!---------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders" :items="infoItems" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">TABLE SYNTAX</div>
        <div style="height:calc(100% - 118px);">
          <div id="infoEditor" style="float:left"></div>
        </div>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      
    </div>
  </div>
</template>

<script>
// import axios from 'axios'

// import EventBus from './event-bus'

export default {
  data() {
    return {
    }
  },
  components: {  },
  mounted () {
    // EventBus.$on(‘EVENT_NAME’, function (payLoad) {
    //   ...
    // });
  },
  computed: {
    clientHeaders () { return this.$store.getters['client/connection'].clientHeaders },
    clientItems () { return this.$store.getters['client/connection'].clientItems },
  },
  watch: {
    // currentConn(value) {
    //   this.$store.dispatch('client/updateCurrentConn', value)
    // }
  },
  methods: {
   onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      // this.$refs['agGrid' + object.charAt(0).toUpperCase() + object.slice(1)].$el.addEventListener('click', this.onGridClick)
      if (['structure','content'].includes(this.tabSelected)) this.gridApi.showLoadingOverlay()
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.originalTarget.classList.add('ag-cell-highlight');
        e.event.originalTarget.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
            e.event.originalTarget.classList.remove('ag-cell-highlight')
            e.event.originalTarget.classList.add('ag-cell-highlight-animation')
            e.event.originalTarget.style.transition = "background-color " + 200 + "ms"

            // Remove animation
            window.setTimeout(function () {
                e.event.originalTarget.classList.remove('ag-cell-highlight-animation')
                e.event.originalTarget.style.transition = null;
            }, 200);
        }, 200);
      }
    }
  },
}
</script>