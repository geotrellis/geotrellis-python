package geopyspark.geotrellis.io

import geopyspark.geotrellis._

import geotrellis.spark._
import geotrellis.spark.io._
import geotrellis.spark.io.cog._
import geotrellis.spark.io.file._
import geotrellis.spark.io.hadoop._
import geotrellis.spark.io.json._
import geotrellis.spark.io.s3._

import spray.json._
import spray.json.DefaultJsonProtocol._

import org.apache.spark._

import scala.collection.JavaConverters._
import collection.JavaConversions._
import java.util.Map

/**
  * Base wrapper class for various types of attribute store wrappers.
  */
class AttributeStoreWrapper(uri: String) {
  val attributeStore: AttributeStore = AttributeStore(uri)

  def readMetadata(name: String, zoom: Int): String = {
    val id = LayerId(name, zoom)
    val header = produceHeader(attributeStore, id)

    val json =
      header.layerType match {
        case COGLayerType =>
          header.keyClass match {
            case "geotrellis.spark.SpatialKey" =>
              attributeStore
                .readMetadata[COGLayerStorageMetadata[SpatialKey]](LayerId(id.name, 0))
                .metadata
                .tileLayerMetadata(id.zoom)
                .toJson
            case "geotrellis.spark.SpaceTimeKey" =>
              attributeStore
                .readMetadata[COGLayerStorageMetadata[SpaceTimeKey]](LayerId(id.name, 0))
                .metadata
                .tileLayerMetadata(id.zoom)
                .toJson
          }
        case _ => attributeStore.readMetadata[JsObject](id)
      }
    json.compactPrint
  }

  /** Read any attribute store value as JSON object.
   * Returns null if attribute is not found in the store.
   */
  def read(layerName: String, zoom: Int, attributeName: String): String = {
    val id = LayerId(layerName, zoom)
    try {
      val json = attributeStore.read[JsValue](id, attributeName)
      return json.compactPrint
    } catch {
      case e: AttributeNotFoundError =>
        return null
    }
  }

  /** Write JSON formatted string into catalog */
  def write(layerName: String, zoom: Int, attributeName: String, value: String): Unit = {
    val id = LayerId(layerName, zoom)
    if (value == null) return
    val json = value.parseJson // ensure we actually have JSON here
    attributeStore.write(id, attributeName, json)
  }

  def delete(layerName: String, zoom: Int, name: String): Unit = {
    val id = LayerId(layerName, zoom)
    attributeStore.delete(id, name)
  }

  def delete(layerName: String, zoom: Int): Unit = {
    val id = LayerId(layerName, zoom)
    attributeStore.delete(id)
  }

  def contains(layerName: String, zoom: Int): Boolean = {
    val id = LayerId(layerName, zoom)
    attributeStore.layerExists(id)
  }
}
